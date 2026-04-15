# User Profile Edit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a user profile edit feature with a header dropdown entry, modal UI, backend profile APIs, database fields, and synced frontend user state.

**Architecture:** Extend the existing auth-backed user model with `nickname`, `phone`, and `bio`, expose authenticated read/update profile endpoints in the auth module, and keep the frontend consistent by adding a dedicated profile modal that reuses the current modal styling and updates the root `currentUser` state. The implementation follows the current single-page pattern in `App.vue` without adding routing or global state libraries.

**Tech Stack:** Vue 3, Vite, Axios, FastAPI, SQLite, Tailwind CSS

---

## File Structure

- Modify `backend/database.py`
  Responsibility: add backward-compatible user table column migration and profile update persistence.
- Modify `backend/api_auth.py`
  Responsibility: extend user response shape and add authenticated profile read/update endpoints plus validation.
- Modify `frontend/src/api/auth.js`
  Responsibility: expose profile fetch/update client helpers and keep localStorage user data in sync.
- Create `frontend/src/components/ProfileModal.vue`
  Responsibility: render the profile editing modal and submit updated profile data.
- Modify `frontend/src/components/AppHeader.vue`
  Responsibility: add the "个人信息" dropdown action and keep menu behavior consistent.
- Modify `frontend/src/App.vue`
  Responsibility: own profile modal visibility, wire header events, and update root user state after profile save.

### Task 1: Backend Schema And Persistence

**Files:**
- Modify: `backend/database.py`

- [ ] **Step 1: Write the failing test**

Create a temporary SQLite database during the test and verify `init_db()` adds the new columns plus `update_user_profile()` persists trimmed values.

```python
import importlib
import os
import sqlite3
import sys


def test_init_db_adds_profile_columns_and_updates_profile(tmp_path):
    sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
    database = importlib.import_module("database")

    db_file = tmp_path / "app.db"
    database.DB_PATH = str(db_file)
    database.init_db()

    with sqlite3.connect(db_file) as conn:
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }
    assert {"nickname", "phone", "bio"}.issubset(columns)

    user = database.create_user("profile@example.com", "hashed")
    updated = database.update_user_profile(
        user["id"],
        nickname="  Alice  ",
        phone=" 13800138000 ",
        bio=" hello world ",
    )

    assert updated["nickname"] == "Alice"
    assert updated["phone"] == "13800138000"
    assert updated["bio"] == "hello world"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_profile_database.py::test_init_db_adds_profile_columns_and_updates_profile -v`
Expected: FAIL because `backend/tests/test_profile_database.py` and `update_user_profile()` do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add a column migration helper and the profile update function to `backend/database.py`.

```python
def _ensure_user_profile_columns(conn):
    existing_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(users)").fetchall()
    }
    for column_name, ddl in (
        ("nickname", "ALTER TABLE users ADD COLUMN nickname TEXT"),
        ("phone", "ALTER TABLE users ADD COLUMN phone TEXT"),
        ("bio", "ALTER TABLE users ADD COLUMN bio TEXT"),
    ):
        if column_name not in existing_columns:
            conn.execute(ddl)


def init_db():
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_vip INTEGER DEFAULT 0,
                vip_expire_at TEXT,
                daily_summary_count INTEGER DEFAULT 0,
                last_summary_date TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            """
        )
        _ensure_user_profile_columns(conn)
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS orders (
                ...
            );
            """
        )


def update_user_profile(user_id: int, nickname: str, phone: str, bio: str) -> dict | None:
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            """
            UPDATE users
            SET nickname = ?, phone = ?, bio = ?, updated_at = ?
            WHERE id = ?
            """,
            (nickname.strip(), phone.strip(), bio.strip(), now, user_id),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_profile_database.py::test_init_db_adds_profile_columns_and_updates_profile -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/database.py backend/tests/test_profile_database.py
git commit -m "feat: add profile fields to user persistence"
```

### Task 2: Backend Profile API

**Files:**
- Modify: `backend/api_auth.py`
- Test: `backend/tests/test_profile_api.py`

- [ ] **Step 1: Write the failing test**

Cover authenticated profile fetch, successful update, and validation errors.

```python
from fastapi.testclient import TestClient

from main import app
from auth import create_token, hash_password
from database import create_user, update_user_profile


client = TestClient(app)


def test_get_profile_requires_login():
    response = client.get("/api/auth/profile")
    assert response.status_code == 401


def test_get_and_update_profile_success():
    user = create_user("api-profile@example.com", hash_password("123456"))
    update_user_profile(user["id"], "初始昵称", "", "")
    token = create_token(user["id"], user["email"])

    get_response = client.get(
        "/api/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 200
    assert get_response.json()["data"]["nickname"] == "初始昵称"

    put_response = client.put(
        "/api/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "nickname": "更新后昵称",
            "phone": "13800138000",
            "bio": "喜欢下载高清视频",
        },
    )
    assert put_response.status_code == 200
    data = put_response.json()["data"]
    assert data["nickname"] == "更新后昵称"
    assert data["phone"] == "13800138000"
    assert data["bio"] == "喜欢下载高清视频"


def test_update_profile_rejects_long_values():
    user = create_user("api-limit@example.com", hash_password("123456"))
    token = create_token(user["id"], user["email"])

    response = client.put(
        "/api/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"nickname": "a" * 31, "phone": "", "bio": ""},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "昵称长度不能超过 30 个字符"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_profile_api.py -v`
Expected: FAIL because `/api/auth/profile` endpoints and profile fields are not implemented.

- [ ] **Step 3: Write minimal implementation**

Extend auth responses and add request validation.

```python
class UpdateProfileRequest(BaseModel):
    nickname: str = ""
    phone: str = ""
    bio: str = ""


def _validate_profile_fields(nickname: str, phone: str, bio: str):
    if len(nickname.strip()) > 30:
        raise HTTPException(status_code=400, detail="昵称长度不能超过 30 个字符")
    if len(phone.strip()) > 20:
        raise HTTPException(status_code=400, detail="手机号长度不能超过 20 个字符")
    if len(bio.strip()) > 200:
        raise HTTPException(status_code=400, detail="个人简介长度不能超过 200 个字符")


def _build_user_response(user: dict) -> dict:
    ...
    return {
        "id": user["id"],
        "email": user["email"],
        "nickname": user.get("nickname") or "",
        "phone": user.get("phone") or "",
        "bio": user.get("bio") or "",
        "is_vip": is_vip,
        "vip_expire_at": vip_expire_at,
    }


@router.get("/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    return {"success": True, "data": _build_user_response(user)}


@router.put("/profile")
async def update_profile(req: UpdateProfileRequest, user: dict = Depends(get_current_user)):
    _validate_profile_fields(req.nickname, req.phone, req.bio)
    updated = update_user_profile(
        user["id"],
        req.nickname,
        req.phone,
        req.bio,
    )
    return {"success": True, "data": _build_user_response(updated)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_profile_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api_auth.py backend/tests/test_profile_api.py
git commit -m "feat: add user profile auth endpoints"
```

### Task 3: Frontend Auth API State Sync

**Files:**
- Modify: `frontend/src/api/auth.js`

- [ ] **Step 1: Write the failing test**

If the project has Vitest configured, add a focused API helper test to verify profile updates overwrite saved user data.

```javascript
import { describe, expect, it, vi } from 'vitest'
import axios from 'axios'
import { saveUser, updateProfile, getSavedUser } from '../src/api/auth'

vi.mock('axios')

describe('auth profile api', () => {
  it('stores updated profile data after save', async () => {
    localStorage.clear()
    saveUser({ id: 1, email: 'user@example.com', nickname: '' })
    axios.put.mockResolvedValue({
      data: {
        data: {
          id: 1,
          email: 'user@example.com',
          nickname: 'Alice',
          phone: '13800138000',
          bio: 'hello',
          is_vip: false,
          vip_expire_at: null,
        },
      },
    })

    await updateProfile({ nickname: 'Alice', phone: '13800138000', bio: 'hello' })

    expect(getSavedUser().nickname).toBe('Alice')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --run auth`
Expected: FAIL because `updateProfile()` and the matching test setup do not exist yet. If no frontend test runner is configured, document that and move to implementation with manual verification.

- [ ] **Step 3: Write minimal implementation**

Add profile API helpers that reuse the existing auth headers and user persistence behavior.

```javascript
export async function fetchProfile() {
  const res = await axios.get('/api/auth/profile', { headers: authHeaders() })
  const user = res.data.data
  saveUser(user)
  return user
}

export async function updateProfile(payload) {
  const res = await axios.put('/api/auth/profile', payload, { headers: authHeaders() })
  const user = res.data.data
  saveUser(user)
  return user
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --run auth`
Expected: PASS if Vitest exists; otherwise no automated frontend API test is available and manual verification is required.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/auth.js
git commit -m "feat: add frontend profile auth api helpers"
```

### Task 4: Profile Modal UI

**Files:**
- Create: `frontend/src/components/ProfileModal.vue`

- [ ] **Step 1: Write the failing test**

If Vue component tests exist, add one to verify the modal renders current values and emits the updated user after save. If no component test setup exists, note the gap and use manual verification.

```javascript
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import ProfileModal from '../src/components/ProfileModal.vue'

vi.mock('../src/api/auth', () => ({
  updateProfile: vi.fn().mockResolvedValue({
    id: 1,
    email: 'user@example.com',
    nickname: 'Alice',
    phone: '13800138000',
    bio: 'hello',
    is_vip: false,
    vip_expire_at: null,
  }),
}))

describe('ProfileModal', () => {
  it('submits updated profile values', async () => {
    const wrapper = mount(ProfileModal, {
      props: {
        visible: true,
        user: { email: 'user@example.com', nickname: '', phone: '', bio: '' },
      },
    })
    await wrapper.find('input[placeholder="请输入昵称"]').setValue('Alice')
    await wrapper.find('form').trigger('submit.prevent')
    expect(wrapper.emitted().success).toBeTruthy()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --run ProfileModal`
Expected: FAIL because `ProfileModal.vue` does not exist yet. If component tests are not configured, document the gap and proceed with manual verification.

- [ ] **Step 3: Write minimal implementation**

Create a modal mirroring the existing auth modal structure.

```vue
<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-[100] flex items-center justify-center" @click.self="$emit('close')">
      <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="$emit('close')"></div>
      <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden animate-modal-in">
        <div class="px-8 pt-8 pb-4">
          <div class="flex items-center justify-between mb-1">
            <h2 class="text-xl font-bold text-text-primary">个人信息</h2>
            <button @click="$emit('close')" class="p-1 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
              ...
            </button>
          </div>
          <p class="text-sm text-text-secondary">编辑你的个人资料信息，邮箱暂不支持修改。</p>
        </div>
        <form @submit.prevent="handleSubmit" class="px-8 pb-8">
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1.5">邮箱地址</label>
              <input :value="user?.email || ''" type="email" disabled class="w-full h-11 px-4 rounded-xl border border-border bg-gray-50 text-sm text-text-secondary" />
            </div>
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1.5">昵称</label>
              <input v-model="nickname" placeholder="请输入昵称" class="w-full h-11 px-4 rounded-xl border border-border bg-white text-sm text-text-primary ..." :disabled="submitting" />
            </div>
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1.5">手机号</label>
              <input v-model="phone" placeholder="请输入手机号" class="w-full h-11 px-4 rounded-xl border border-border bg-white text-sm text-text-primary ..." :disabled="submitting" />
            </div>
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1.5">个人简介</label>
              <textarea v-model="bio" rows="4" placeholder="介绍一下你自己" class="w-full px-4 py-3 rounded-xl border border-border bg-white text-sm text-text-primary resize-none ..." :disabled="submitting"></textarea>
            </div>
          </div>
          <div v-if="error" class="mt-4 p-3 rounded-xl bg-red-50 border border-red-100">
            <p class="text-sm text-red-600">{{ error }}</p>
          </div>
          <button type="submit" :disabled="submitting" class="w-full h-11 mt-6 rounded-full bg-primary text-white text-sm font-semibold ...">
            {{ submitting ? '保存中...' : '保存修改' }}
          </button>
        </form>
      </div>
    </div>
  </Teleport>
</template>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --run ProfileModal`
Expected: PASS if frontend component tests exist; otherwise verify manually in the browser.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ProfileModal.vue
git commit -m "feat: add profile edit modal"
```

### Task 5: Header And App Integration

**Files:**
- Modify: `frontend/src/components/AppHeader.vue`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: Write the failing test**

If app-level UI tests exist, write one that verifies a logged-in user can open the profile modal from the header menu. If not, use manual verification.

```javascript
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AppHeader from '../src/components/AppHeader.vue'

describe('AppHeader profile action', () => {
  it('emits open-profile from the user menu', async () => {
    const wrapper = mount(AppHeader, {
      props: {
        user: { email: 'user@example.com', is_vip: false, vip_expire_at: null },
      },
    })

    await wrapper.find('button').trigger('click')
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted()['open-profile']).toBeTruthy()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --run AppHeader`
Expected: FAIL because the header does not emit `open-profile` yet. If frontend test setup is absent, document the gap and verify manually.

- [ ] **Step 3: Write minimal implementation**

Add the new menu item and wire the modal in `App.vue`.

```vue
<!-- AppHeader.vue -->
<button
  @click="menuOpen = false; $emit('open-profile')"
  class="w-full text-left px-4 py-2.5 text-sm text-text-secondary hover:bg-gray-50 transition-colors cursor-pointer flex items-center gap-2"
>
  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">...</svg>
  个人信息
</button>
```

```vue
<!-- App.vue -->
<AppHeader
  :user="currentUser"
  @login="showAuthModal('login')"
  @register="showAuthModal('register')"
  @logout="handleLogout"
  @open-vip="handleOpenVip"
  @open-profile="profileModalVisible = true"
/>

<ProfileModal
  :visible="profileModalVisible"
  :user="currentUser"
  @close="profileModalVisible = false"
  @success="handleProfileSuccess"
/>
```

```javascript
import ProfileModal from './components/ProfileModal.vue'

const profileModalVisible = ref(false)

function handleProfileSuccess(user) {
  currentUser.value = user
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --run AppHeader`
Expected: PASS if frontend UI tests exist; otherwise manual verification passes when the menu entry opens the modal and saved data updates the header state.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/AppHeader.vue frontend/src/App.vue
git commit -m "feat: wire profile editing into header flow"
```

### Task 6: Verification

**Files:**
- Verify only

- [ ] **Step 1: Run backend profile tests**

Run: `python -m pytest backend/tests/test_profile_database.py backend/tests/test_profile_api.py -v`
Expected: PASS

- [ ] **Step 2: Run frontend checks**

Run: `npm run build`
Expected: build succeeds without Vue compile errors

- [ ] **Step 3: Manual smoke test**

Run the app locally and verify:

```text
1. Register or log in with a user.
2. Open the header dropdown and click "个人信息".
3. Confirm email is read-only and existing values are prefilled.
4. Save nickname/phone/bio and confirm the modal closes.
5. Refresh the page and confirm data is still present.
6. Try a nickname longer than 30 characters and confirm the modal shows the backend error message.
```

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "test: verify user profile edit flow"
```
