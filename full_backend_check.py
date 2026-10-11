"""
FleetSet backend verification script.

Run from the backend project root:

    python full_backend_check.py

For live API checks:

    $env:FLEETSET_BASE_URL="http://127.0.0.1:8000"
    $env:FLEETSET_TEST_EMAIL="driver.test@fleetset.com"
    $env:FLEETSET_TEST_PASSWORD="TempPassword123!"
    python full_backend_check.py --live

Optional management-role credentials:

    $env:FLEETSET_SUPER_ADMIN_EMAIL="arun.menon@fleetset.com"
    $env:FLEETSET_SUPER_ADMIN_PASSWORD="TempPassword123!"

    $env:FLEETSET_BRANCH_ADMIN_EMAIL="vattappara.admin@fleetset.com"
    $env:FLEETSET_BRANCH_ADMIN_PASSWORD="TempPassword123!"

The live mode is intentionally read-only. It does not create, update, delete,
activate, or deactivate production data.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import py_compile
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path



ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "app"


EXPECTED_BRANCH_MODELS = {
    "Driver",
    "Vehicle",
    "Trip",
    "FuelLog",
    "MaintenanceRecord",
    "VehicleDocument",
    "DriverVehicleAssignment",
    "Notification",
}


PUBLIC_ROUTES = {
    ("POST", "/auth/login"),
    ("GET", "/docs"),
    ("GET", "/docs/oauth2-redirect"),
    ("GET", "/openapi.json"),
    ("GET", "/redoc"),
}


def ok(message: str) -> None:
    print(f"[PASS] {message}")


def fail(message: str) -> None:
    print(f"[FAIL] {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def compile_check() -> bool:
    print("\n== Python compilation ==")

    failures = []

    for path in APP_DIR.rglob("*.py"):
        try:
            py_compile.compile(
                str(path),
                doraise=True,
            )
        except Exception as exc:
            failures.append(
                (
                    path,
                    exc,
                )
            )

    if failures:
        for path, exc in failures:
            fail(
                f"{path.relative_to(ROOT)} -> {exc}"
            )
        return False

    ok("All app Python files compile successfully")
    return True


def import_check():
    print("\n== FastAPI import ==")

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        module = importlib.import_module("app.main")
        app = module.app

        ok(
            f"FastAPI app imported: "
            f"{app.title} {app.version}"
        )

        return app

    except Exception as exc:
        fail(
            f"Could not import app.main: {exc}"
        )
        return None


def route_check(app) -> bool:
    print("\n== Route inventory ==")

    routes = []

    try:
        openapi = app.openapi()
        paths = openapi.get("paths", {})

        for path, path_item in paths.items():
            for method in path_item:
                method_upper = method.upper()

                if method_upper in {
                    "HEAD",
                    "OPTIONS",
                }:
                    continue

                routes.append(
                    (
                        method_upper,
                        path,
                    )
                )

    except Exception as exc:
        fail(
            f"Could not build OpenAPI route inventory: {exc}"
        )
        return False

    routes = sorted(set(routes))

    print(
        f"Registered HTTP routes: {len(routes)}"
    )

    for method, path in routes:
        marker = (
            "PUBLIC"
            if (method, path) in PUBLIC_ROUTES
            else "AUTH"
        )

        print(
            f"  [{marker}] {method:<6} {path}"
        )

    if len(routes) < 20:
        warn(
            "The application has fewer than 20 registered "
            "HTTP routes. Review the route inventory above."
        )
    else:
        ok(
            f"Discovered {len(routes)} registered "
            "HTTP route/method combinations"
        )

    auth_route_count = 0
    unaudited_routes = []

    for route in app.routes:
        path = getattr(
            route,
            "path",
            None,
        )

        methods = getattr(
            route,
            "methods",
            set(),
        )

        if not path or not methods:
            continue

        dependant = getattr(
            route,
            "dependant",
            None,
        )

        dependency_names = []

        def collect_dependencies(dependant_node):
            if dependant_node is None:
                return

            dependencies = getattr(
                dependant_node,
                "dependencies",
                [],
            ) or []

            for dependency in dependencies:
                call = getattr(
                    dependency,
                    "call",
                    None,
                )

                if call is not None:
                    dependency_names.append(
                        getattr(
                            call,
                            "__name__",
                            str(call),
                        )
                    )

                collect_dependencies(
                    dependency
                )

        collect_dependencies(dependant)

        has_auth = any(
            name in {
                "get_current_user",
                "require_roles",
            }
            for name in dependency_names
        )

        for method in methods:
            method_upper = method.upper()

            if method_upper in {
                "HEAD",
                "OPTIONS",
            }:
                continue

            if (
                method_upper,
                path,
            ) in PUBLIC_ROUTES:
                continue

            if has_auth:
                auth_route_count += 1
            else:
                unaudited_routes.append(
                    (
                        method_upper,
                        path,
                        dependency_names,
                    )
                )

    if unaudited_routes:
        warn(
            f"{len(unaudited_routes)} non-public route/method "
            "combination(s) have no obvious auth dependency."
        )

        for method, path, dependencies in (
            unaudited_routes
        ):
            warn(
                f"  {method} {path} "
                f"dependencies={dependencies}"
            )

        warn(
            "This is an audit warning, not automatically a failure. "
            "Some routes intentionally perform authorization inside "
            "their service layer."
        )

    else:
        ok(
            "All non-public application routes have "
            "an authentication dependency"
        )

    if auth_route_count:
        ok(
            f"Authentication dependency audit inspected "
            f"{auth_route_count} protected route/method combinations"
        )

    return True


def branch_model_check() -> bool:
    print("\n== Branch-scope model audit ==")

    failures = []

    for model_name in sorted(
        EXPECTED_BRANCH_MODELS
    ):
        found = None

        for path in (
            APP_DIR / "models"
        ).glob("*.py"):

            text = path.read_text(
                encoding="utf-8",
                errors="replace",
            )

            if f"class {model_name}" in text:
                found = text
                break

        if found is None:
            failures.append(
                f"{model_name}: model not found"
            )

        elif "branch_id" not in found:
            failures.append(
                f"{model_name}: branch_id is missing"
            )

    if failures:
        for item in failures:
            fail(item)

        return False

    ok(
        "All branch-scoped operational models "
        "contain branch_id"
    )

    return True


def api_request(
    base_url: str,
    path: str,
    method: str = "GET",
    token: str | None = None,
    form: dict | None = None,
):
    url = (
        base_url.rstrip("/")
        + path
    )

    data = None

    headers = {
        "Accept": "application/json",
    }

    if form is not None:
        data = urllib.parse.urlencode(
            form
        ).encode()

        headers["Content-Type"] = (
            "application/x-www-form-urlencoded"
        )

    if token:
        headers["Authorization"] = (
            f"Bearer {token}"
        )

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=10,
        ) as response:

            raw = response.read().decode(
                "utf-8"
            )

            try:
                payload = (
                    json.loads(raw)
                    if raw
                    else None
                )
            except json.JSONDecodeError:
                payload = raw

            return response.status, payload

    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(
            "utf-8"
        )

        try:
            payload = (
                json.loads(raw)
                if raw
                else None
            )
        except json.JSONDecodeError:
            payload = raw

        return exc.code, payload

    except Exception as exc:
        return 0, {
            "detail": str(exc)
        }


def is_empty_404(payload) -> bool:
    if not isinstance(payload, dict):
        return False

    detail = str(
        payload.get(
            "detail",
            "",
        )
    ).lower()

    return "no " in detail


def assert_branch_records(
    name: str,
    records,
    branch_id: str,
) -> bool:

    if not isinstance(records, list):
        warn(
            f"{name}: response is not a list"
        )
        return False

    mismatches = []

    for item in records:
        if not isinstance(item, dict):
            continue

        item_branch = item.get(
            "branch_id"
        )

        if item_branch is None:
            continue

        if str(item_branch) != str(branch_id):
            mismatches.append(
                item_branch
            )

    if mismatches:
        fail(
            f"{name}: returned records outside "
            f"current branch ({mismatches[:3]})"
        )
        return False

    ok(
        f"{name}: {len(records)} record(s), "
        "all within current branch"
    )

    return True


def assert_branch_list(
    name: str,
    records,
    branch_id: str,
) -> bool:

    if not isinstance(records, list):
        warn(
            f"{name}: response is not a list"
        )
        return False

    mismatches = []

    for item in records:
        if not isinstance(item, dict):
            continue

        item_id = item.get(
            "id"
        )

        if item_id is None:
            continue

        if str(item_id) != str(branch_id):
            mismatches.append(
                item_id
            )

    if mismatches:
        fail(
            f"{name}: returned branches outside "
            f"current branch ({mismatches[:3]})"
        )
        return False

    ok(
        f"{name}: {len(records)} branch record(s), "
        "all within current branch"
    )

    return True


def login_user(
    base_url: str,
    email: str,
    password: str,
):
    status, payload = api_request(
        base_url,
        "/auth/login",
        method="POST",
        form={
            "username": email,
            "password": password,
        },
    )

    if (
        status != 200
        or not isinstance(payload, dict)
        or not payload.get("access_token")
    ):
        fail(
            f"Login failed for {email}: "
            f"HTTP {status} {payload}"
        )
        return None

    return payload["access_token"]


def get_current_user(
    base_url: str,
    token: str,
):
    status, payload = api_request(
        base_url,
        "/auth/me",
        token=token,
    )

    if (
        status != 200
        or not isinstance(payload, dict)
    ):
        fail(
            f"/auth/me failed: "
            f"HTTP {status} {payload}"
        )
        return None

    return payload


def test_resource(
    base_url: str,
    token: str,
    name: str,
    path: str,
    branch_id: str | None,
    branch_records: bool = True,
):
    status, payload = api_request(
        base_url,
        path,
        token=token,
    )

    if status == 200:

        if name == "assignments":
            records = (
                payload.get(
                    "assignments",
                    [],
                )
                if isinstance(payload, dict)
                else []
            )

            if branch_id:
                return assert_branch_records(
                    name,
                    records,
                    branch_id,
                )

            ok(
                f"{name}: HTTP 200"
            )
            return True

        if (
            branch_records
            and branch_id
        ):
            return assert_branch_records(
                name,
                payload,
                branch_id,
            )

        ok(
            f"{name}: HTTP 200"
        )
        return True

    if (
        status == 404
        and is_empty_404(payload)
    ):
        ok(
            f"{name}: empty resource reported as 404"
        )
        return True

    fail(
        f"{name}: HTTP {status} {payload}"
    )
    return False


def test_branch_endpoint(
    base_url: str,
    token: str,
    company_id: str,
    role_name: str,
    branch_id: str | None,
):
    path = (
        f"/branches/company/{company_id}"
    )

    status, payload = api_request(
        base_url,
        path,
        token=token,
    )

    if (
        status == 404
        and is_empty_404(payload)
    ):
        ok(
            "branches: empty resource reported as 404"
        )
        return True, None

    if status != 200:
        fail(
            f"branches: HTTP {status} {payload}"
        )
        return False, None

    if not isinstance(payload, list):
        fail(
            "branches: response is not a list"
        )
        return False, None

    if role_name in {
        "BRANCH_ADMIN",
        "DRIVER",
    }:

        if not branch_id:
            fail(
                f"branches: {role_name} has no branch_id"
            )
            return False, None

        result = assert_branch_list(
            "branches",
            payload,
            branch_id,
        )

        return result, branch_id

    if role_name == "SUPER_ADMIN":

        invalid = []

        for branch in payload:
            if not isinstance(branch, dict):
                continue

            item_company_id = branch.get(
                "company_id"
            )

            if (
                item_company_id is not None
                and str(item_company_id)
                != str(company_id)
            ):
                invalid.append(
                    item_company_id
                )

        if invalid:
            fail(
                "branches: SUPER_ADMIN received "
                f"branches outside company ({invalid[:3]})"
            )
            return False, None

        ok(
            f"branches: {len(payload)} branch record(s), "
            "all within current company"
        )

        selected_branch_id = None

        for branch in payload:
            if not isinstance(branch, dict):
                continue

            candidate = branch.get("id")

            if candidate:
                selected_branch_id = str(candidate)
                break

        if selected_branch_id:
            ok(
                "SUPER_ADMIN branch report test will use "
                f"branch_id={selected_branch_id}"
            )
        else:
            warn(
                "SUPER_ADMIN company has no branch records; "
                "branch-specific report test will be skipped"
            )

        return True, selected_branch_id

    ok(
        f"branches: {len(payload)} branch record(s)"
    )

    return True, None


def test_daily_report(
    base_url: str,
    token: str,
    company_id: str,
    role_name: str,
    branch_id: str | None,
    report_branch_id: str | None = None,
) -> bool:

    today = date.today().isoformat()

    base_path = (
        f"/reports/{company_id}/daily"
        f"?report_date={today}"
    )

    if role_name == "SUPER_ADMIN":

        status, payload = api_request(
            base_url,
            base_path,
            token=token,
        )

        if status == 200:
            ok(
                "SUPER_ADMIN company-wide daily report "
                "responded successfully"
            )

        elif (
            status == 404
            and is_empty_404(payload)
        ):
            ok(
                "SUPER_ADMIN company-wide daily report "
                "returned expected empty-data 404"
            )

        else:
            fail(
                "SUPER_ADMIN company-wide daily report: "
                f"HTTP {status} {payload}"
            )
            return False

        if not report_branch_id:
            warn(
                "SUPER_ADMIN branch-specific report test "
                "was skipped because no branch was available"
            )
            return True

        branch_path = (
            f"{base_path}"
            f"&branch_id={urllib.parse.quote(str(report_branch_id))}"
        )

        status, payload = api_request(
            base_url,
            branch_path,
            token=token,
        )

        if status == 200:
            ok(
                "SUPER_ADMIN branch-scoped daily report "
                "responded successfully"
            )
            return True

        if (
            status == 404
            and is_empty_404(payload)
        ):
            ok(
                "SUPER_ADMIN branch-scoped daily report "
                "returned expected empty-data 404"
            )
            return True

        fail(
            "SUPER_ADMIN branch-scoped daily report: "
            f"HTTP {status} {payload}"
        )
        return False

    if role_name == "BRANCH_ADMIN":

        if not branch_id:
            fail(
                "BRANCH_ADMIN has no branch_id"
            )
            return False

        branch_path = (
            f"{base_path}"
            f"&branch_id={urllib.parse.quote(str(branch_id))}"
        )

        status, payload = api_request(
            base_url,
            branch_path,
            token=token,
        )

        if status == 200:
            ok(
                "BRANCH_ADMIN own-branch daily report "
                "responded successfully"
            )
            return True

        if (
            status == 404
            and is_empty_404(payload)
        ):
            ok(
                "BRANCH_ADMIN own-branch daily report "
                "returned expected empty-data 404"
            )
            return True

        fail(
            "BRANCH_ADMIN own-branch daily report: "
            f"HTTP {status} {payload}"
        )
        return False

    if role_name == "DRIVER":

        status, payload = api_request(
            base_url,
            base_path,
            token=token,
        )

        if status == 403:
            ok(
                "DRIVER daily report correctly denied with 403"
            )
            return True

        fail(
            "DRIVER daily report expected 403, "
            f"received HTTP {status} {payload}"
        )
        return False

    return True


def live_check_for_user(
    base_url: str,
    email: str,
    password: str,
) -> bool:

    print(
        f"\n== Live check: {email} =="
    )

    token = login_user(
        base_url,
        email,
        password,
    )

    if token is None:
        return False

    ok("Authentication succeeded")

    me = get_current_user(
        base_url,
        token,
    )

    if me is None:
        return False

    company_id = me.get(
        "company_id"
    )

    branch_id = me.get(
        "branch_id"
    )

    role_name = me.get(
        "role_name"
    )

    if not company_id:
        fail(
            "/auth/me did not return company_id"
        )
        return False

    if role_name in {
        "BRANCH_ADMIN",
        "DRIVER",
    } and not branch_id:
        fail(
            f"{role_name} user has no branch_id"
        )
        return False

    ok(
        f"/auth/me returned "
        f"role={role_name}, "
        f"company_id={company_id}, "
        f"branch_id={branch_id}"
    )

    success = True

    checks = [
        (
            "vehicles",
            f"/vehicles/{company_id}/all",
            True,
        ),
        (
            "drivers",
            f"/drivers/{company_id}",
            True,
        ),
        (
            "assignments",
            f"/driver-vehicle-assignments/{company_id}",
            False,
        ),
        (
            "fuel",
            f"/fuel-logs/{company_id}/all",
            True,
        ),
        (
            "maintenance",
            f"/maintenance/{company_id}/all",
            True,
        ),
    ]

    if role_name == "BRANCH_ADMIN":
        checks.append(
            (
                "documents",
                f"/vehicle-documents/{company_id}/all",
                True,
            )
        )

    for (
        name,
        path,
        branch_records,
    ) in checks:

        result = test_resource(
            base_url=base_url,
            token=token,
            name=name,
            path=path,
            branch_id=branch_id,
            branch_records=branch_records,
        )

        success = (
            result
            and success
        )

    branch_result, report_branch_id = (
        test_branch_endpoint(
            base_url=base_url,
            token=token,
            company_id=company_id,
            role_name=role_name,
            branch_id=branch_id,
        )
    )

    success = (
        branch_result
        and success
    )

    report_result = test_daily_report(
        base_url=base_url,
        token=token,
        company_id=company_id,
        role_name=role_name,
        branch_id=branch_id,
        report_branch_id=report_branch_id,
    )

    success = (
        report_result
        and success
    )

    return success


def live_check() -> bool:
    print("\n== Live read-only API smoke test ==")

    base_url = os.getenv(
        "FLEETSET_BASE_URL",
        "http://127.0.0.1:8000",
    )

    credentials = []

    driver_email = os.getenv(
        "FLEETSET_TEST_EMAIL"
    )

    driver_password = os.getenv(
        "FLEETSET_TEST_PASSWORD"
    )

    super_admin_email = os.getenv(
        "FLEETSET_SUPER_ADMIN_EMAIL"
    )

    super_admin_password = os.getenv(
        "FLEETSET_SUPER_ADMIN_PASSWORD"
    )

    branch_admin_email = os.getenv(
        "FLEETSET_BRANCH_ADMIN_EMAIL"
    )

    branch_admin_password = os.getenv(
        "FLEETSET_BRANCH_ADMIN_PASSWORD"
    )

    if (
        driver_email
        and driver_password
    ):
        credentials.append(
            (
                driver_email,
                driver_password,
            )
        )

    if (
        super_admin_email
        and super_admin_password
    ):
        credentials.append(
            (
                super_admin_email,
                super_admin_password,
            )
        )

    if (
        branch_admin_email
        and branch_admin_password
    ):
        credentials.append(
            (
                branch_admin_email,
                branch_admin_password,
            )
        )

    if not credentials:
        warn(
            "No live credentials configured. "
            "Set FLEETSET_TEST_EMAIL/FLEETSET_TEST_PASSWORD "
            "or management-role credentials."
        )
        return True

    success = True

    for email, password in credentials:

        result = live_check_for_user(
            base_url=base_url,
            email=email,
            password=password,
        )

        success = (
            result
            and success
        )

    return success


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--live",
        action="store_true",
        help="Run read-only API checks",
    )

    args = parser.parse_args()

    results = [
        compile_check(),
    ]

    app = import_check()

    if app is None:
        results.append(False)

    else:
        results.append(
            route_check(app)
        )

        results.append(
            branch_model_check()
        )

    if args.live:
        results.append(
            live_check()
        )

    print("\n== Summary ==")

    if all(results):
        print(
            "FleetSet backend check completed successfully."
        )
        return 0

    print(
        "FleetSet backend check found one or more failures."
    )

    return 1


if __name__ == "__main__":
    raise SystemExit(main())