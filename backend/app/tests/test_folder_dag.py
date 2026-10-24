import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resource import Resource
from app.models.user import User
from app.tests.conftest import get_auth_token


@pytest.mark.asyncio
async def test_create_root_and_nested_subfolders(async_client: AsyncClient):
    """Test creating root and nested subfolders."""
    token = await get_auth_token(async_client, "student@amu.edu")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create root folder
    res1 = await async_client.post("/api/v1/folders", headers=headers, json={"name": "Root Folder"})
    assert res1.status_code == 201
    root = res1.json()
    assert root["parent_folder_id"] is None

    # 2. Create subfolder
    res2 = await async_client.post(
        "/api/v1/folders",
        headers=headers,
        json={"name": "Subfolder 1", "parent_folder_id": root["folder_id"]},
    )
    assert res2.status_code == 201
    sub = res2.json()
    assert sub["parent_folder_id"] == root["folder_id"]


@pytest.mark.asyncio
async def test_breadcrumbs_recursive_cte(async_client: AsyncClient):
    """Test recursive CTE constructing breadcrumb hierarchy."""
    token = await get_auth_token(async_client, "student@amu.edu")
    headers = {"Authorization": f"Bearer {token}"}

    # Hierarchy: A -> B -> C
    f_a = (
        await async_client.post("/api/v1/folders", headers=headers, json={"name": "Dept CS"})
    ).json()
    f_b = (
        await async_client.post(
            "/api/v1/folders",
            headers=headers,
            json={"name": "Semester 1", "parent_folder_id": f_a["folder_id"]},
        )
    ).json()
    f_c = (
        await async_client.post(
            "/api/v1/folders",
            headers=headers,
            json={"name": "Algorithms", "parent_folder_id": f_b["folder_id"]},
        )
    ).json()

    contents_res = await async_client.get(
        f"/api/v1/folders/{f_c['folder_id']}/contents", headers=headers
    )
    assert contents_res.status_code == 200
    data = contents_res.json()
    breadcrumbs = data["breadcrumbs"]
    assert len(breadcrumbs) == 3
    assert breadcrumbs[0]["name"] == "Dept CS"
    assert breadcrumbs[1]["name"] == "Semester 1"
    assert breadcrumbs[2]["name"] == "Algorithms"


@pytest.mark.asyncio
async def test_ec04_1_self_parenting_rejected(async_client: AsyncClient):
    """EC-04.1: Moving folder into itself must be rejected with HTTP 400."""
    token = await get_auth_token(async_client, "student@amu.edu")
    headers = {"Authorization": f"Bearer {token}"}

    folder = (
        await async_client.post("/api/v1/folders", headers=headers, json={"name": "Self Loop Test"})
    ).json()

    res = await async_client.patch(
        f"/api/v1/folders/{folder['folder_id']}",
        headers=headers,
        json={"parent_folder_id": folder["folder_id"]},
    )
    assert res.status_code == 400
    assert "circular hierarchy" in res.json()["detail"]


@pytest.mark.asyncio
async def test_ec04_2_deep_tree_cycle_rejected(async_client: AsyncClient):
    """EC-04.2: Moving ancestor folder into its descendant must be rejected with HTTP 400."""
    token = await get_auth_token(async_client, "student@amu.edu")
    headers = {"Authorization": f"Bearer {token}"}

    # A -> B -> C
    f_a = (
        await async_client.post("/api/v1/folders", headers=headers, json={"name": "Grandparent A"})
    ).json()
    f_b = (
        await async_client.post(
            "/api/v1/folders",
            headers=headers,
            json={"name": "Parent B", "parent_folder_id": f_a["folder_id"]},
        )
    ).json()
    f_c = (
        await async_client.post(
            "/api/v1/folders",
            headers=headers,
            json={"name": "Child C", "parent_folder_id": f_b["folder_id"]},
        )
    ).json()

    # Attempt to move A under C (making A a child of C -> circular loop)
    res = await async_client.patch(
        f"/api/v1/folders/{f_a['folder_id']}",
        headers=headers,
        json={"parent_folder_id": f_c["folder_id"]},
    )
    assert res.status_code == 400
    assert "circular hierarchy" in res.json()["detail"]


@pytest.mark.asyncio
async def test_ec04_3_non_empty_deletion_rejected(
    async_client: AsyncClient, db_session: AsyncSession
):
    """EC-04.3: Deleting a non-empty folder must be rejected with HTTP 409 Conflict (SD-09)."""
    token = await get_auth_token(async_client, "student@amu.edu")
    headers = {"Authorization": f"Bearer {token}"}

    # Case 1: Folder containing subfolder
    parent = (
        await async_client.post("/api/v1/folders", headers=headers, json={"name": "Parent Folder"})
    ).json()
    await async_client.post(
        "/api/v1/folders",
        headers=headers,
        json={"name": "Sub Child", "parent_folder_id": parent["folder_id"]},
    )

    del_res = await async_client.delete(f"/api/v1/folders/{parent['folder_id']}", headers=headers)
    assert del_res.status_code == 409
    assert "not empty" in del_res.json()["detail"]

    # Case 2: Folder containing a resource
    single_folder = (
        await async_client.post(
            "/api/v1/folders", headers=headers, json={"name": "Resource Holding Folder"}
        )
    ).json()

    # Query student user
    student = await db_session.scalar(select(User).where(User.email == "student@amu.edu"))
    assert student is not None
    res_obj = Resource(
        owner_id=student.user_id,
        folder_id=single_folder["folder_id"],
        title="Inside Folder Resource",
        status="PRIVATE",
        visibility="PRIVATE",
    )
    db_session.add(res_obj)
    await db_session.commit()

    del_res2 = await async_client.delete(
        f"/api/v1/folders/{single_folder['folder_id']}", headers=headers
    )
    assert del_res2.status_code == 409
    assert "not empty" in del_res2.json()["detail"]


@pytest.mark.asyncio
async def test_ec04_4_cross_tenant_folder_access_blocked(async_client: AsyncClient):
    """EC-04.4: Student cannot access, modify, or delete another student's private folder."""
    # Student A creates folder
    token_a = await get_auth_token(async_client, "student@amu.edu")
    folder_a = (
        await async_client.post(
            "/api/v1/folders",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"name": "Student A Private Notes"},
        )
    ).json()

    # Teacher or another user attempts to inspect or delete Student A's private folder
    token_teacher = await get_auth_token(async_client, "teacher@amu.edu")
    headers_teacher = {"Authorization": f"Bearer {token_teacher}"}

    # 1. Content access blocked
    res1 = await async_client.get(
        f"/api/v1/folders/{folder_a['folder_id']}/contents", headers=headers_teacher
    )
    assert res1.status_code == 403

    # 2. Rename/move blocked
    res2 = await async_client.patch(
        f"/api/v1/folders/{folder_a['folder_id']}",
        headers=headers_teacher,
        json={"name": "Tampered Name"},
    )
    assert res2.status_code == 403

    # 3. Deletion blocked
    res3 = await async_client.delete(
        f"/api/v1/folders/{folder_a['folder_id']}", headers=headers_teacher
    )
    assert res3.status_code == 403


@pytest.mark.asyncio
async def test_delete_empty_folder_success(async_client: AsyncClient):
    """Test successful deletion of an empty folder."""
    token = await get_auth_token(async_client, "student@amu.edu")
    headers = {"Authorization": f"Bearer {token}"}

    folder = (
        await async_client.post(
            "/api/v1/folders", headers=headers, json={"name": "Temporary Folder"}
        )
    ).json()

    del_res = await async_client.delete(f"/api/v1/folders/{folder['folder_id']}", headers=headers)
    assert del_res.status_code == 200
    assert "deleted successfully" in del_res.json()["message"]


@pytest.mark.asyncio
async def test_get_folder_by_id_metadata(async_client: AsyncClient):
    """Test retrieving single folder metadata by ID."""
    token = await get_auth_token(async_client, "student@amu.edu")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await async_client.post(
        "/api/v1/folders", headers=headers, json={"name": "Metadata Test Folder"}
    )
    folder_id = create_res.json()["folder_id"]

    get_res = await async_client.get(f"/api/v1/folders/{folder_id}", headers=headers)
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["folder_id"] == folder_id
    assert data["name"] == "Metadata Test Folder"
