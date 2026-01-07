# COMPLETE PROJECT DOCUMENTATION
## FlowTrack - End-to-End System Documentation

**Version:** 1.0  
**Date:** January 2025  
**Purpose:** Complete step-by-step documentation of all functionalities from registration to every feature

---

## TABLE OF CONTENTS

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Registration & Authentication Flow](#3-registration--authentication-flow)
4. [User Portal Functionalities](#4-user-portal-functionalities)
5. [Admin Portal Functionalities](#5-admin-portal-functionalities)
6. [Database Schema & Data Flow](#6-database-schema--data-flow)
7. [API Endpoints Reference](#7-api-endpoints-reference)
8. [Bidirectional Sync Mechanisms](#8-bidirectional-sync-mechanisms)

---

## 1. PROJECT OVERVIEW

### 1.1 What is FlowTrack?
FlowTrack is a project management and asset tracking system with two portals:
- **User Portal** (`frontend/`): For regular users to manage their projects, tickets, and assets
- **Admin Portal** (`admin/`): For administrators to manage all users, projects, tickets, and assets across the system

### 1.2 Technology Stack
- **Frontend:** React.js (User Portal + Admin Portal)
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL
- **Authentication:** bcrypt password hashing

### 1.3 Project Structure
```
ticketflow/
├── frontend/          # User Portal React App
├── admin/             # Admin Portal React App
├── backend/           # FastAPI Backend
│   └── app/
│       ├── main.py    # Main FastAPI application with all routes
│       ├── models.py  # SQLAlchemy database models
│       ├── schemas.py # Pydantic schemas for request/response
│       ├── crud.py    # Database operations (Create, Read, Update, Delete)
│       └── database.py # Database connection setup
└── DATABASE_SCHEMA.sql # Complete database schema
```

---

## 2. SYSTEM ARCHITECTURE

### 2.1 How Frontend Connects to Backend

**API Configuration File:** `frontend/src/config/api.js`
- **Base URL:** `http://localhost:8000` (configurable via environment variable)
- **Purpose:** Centralized API endpoint configuration
- **Key Functions:**
  - `buildUrl(endpoint)`: Builds full URL from endpoint path
  - `apiRequest(url, options)`: Makes HTTP requests with error handling

**Example Connection:**
```javascript
// Frontend makes request
const response = await fetch(`${API_CONFIG.BASE_URL}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
```

### 2.2 Backend FastAPI Setup

**Main File:** `backend/app/main.py`

**Key Components:**
1. **CORS Middleware:** Allows frontend to communicate with backend
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # Allows all origins
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Database Session Dependency:**
   ```python
   async def get_db() -> AsyncSession:
       async with database.AsyncSessionLocal() as session:
           yield session
   ```

3. **Route Handlers:** Each route uses `Depends(get_db)` to get database session

---

## 3. REGISTRATION & AUTHENTICATION FLOW

### 3.1 USER PORTAL REGISTRATION

#### Step 1: User Fills Registration Form
**File:** `frontend/src/components/auth/Login.js`

**Location in Code:**
- Lines 1605-1676: Registration form UI
- User enters: Full Name, Email, Password

**Form Submission Handler:**
```javascript
const handleRegister = async (e) => {
  e.preventDefault();
  await register(email, password, fullName);  // Calls AuthContext
  navigate('/for-you');
};
```

#### Step 2: Frontend Calls AuthContext
**File:** `frontend/src/context/AuthContext.js`

**Location in Code:**
- Lines 102-167: `register()` function

**What Happens:**
1. Makes POST request to backend:
   ```javascript
   const response = await fetch(`${API_CONFIG.BASE_URL}/auth/register`, {
     method: "POST",
     headers: { "Content-Type": "application/json" },
     body: JSON.stringify({
       email: email,
       password: password,
       full_name: fullName,
     }),
   });
   ```

2. Backend URL: `http://localhost:8000/auth/register`

#### Step 3: Backend Receives Registration Request
**File:** `backend/app/main.py`

**Location in Code:**
- Lines 161-194: `register_user()` endpoint

**Endpoint:** `POST /auth/register`

**What Happens:**
1. Validates input (email, password length)
2. Checks if user already exists:
   ```python
   existing_user = await crud.get_user_by_email(db, user_in.email)
   ```
3. Creates new user:
   ```python
   created_user = await crud.create_user(db, user_in)
   ```
4. Returns user data (without password)

#### Step 4: Database Operation
**File:** `backend/app/crud.py`

**Function:** `create_user()`

**What Happens:**
1. Hashes password using bcrypt:
   ```python
   hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")
   ```
2. Creates record in `users` table:
   ```python
   user = models.User(
       email=user_in.email,
       hashed_password=hashed_password,
       full_name=user_in.full_name
   )
   session.add(user)
   await session.commit()
   ```

#### Step 5: Response Back to Frontend
1. Backend returns: `{ id, email, full_name }`
2. Frontend stores in localStorage:
   ```javascript
   localStorage.setItem("user", JSON.stringify(frontendUserData));
   ```
3. User is redirected to `/for-you` (dashboard)

**Database Table:** `users`
- Stores: `id`, `email`, `hashed_password`, `full_name`, `created_at`

---

### 3.2 ADMIN PORTAL REGISTRATION

#### Step 1: Admin Fills Registration Form
**File:** `admin/src/components/auth/Registration.js`

**Location in Code:**
- Lines 12-40: Registration handler

**Form Submission:**
```javascript
const response = await fetch('http://localhost:8000/admin/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    full_name: fullName,
    email: email,
    password: password,
  }),
});
```

#### Step 2: Backend Admin Registration
**File:** `backend/app/main.py`

**Location in Code:**
- Lines 284-302: `register_admin()` endpoint

**Endpoint:** `POST /admin/register`

**What Happens:**
1. Checks if admin exists
2. Creates admin in `admin_registrations` table
3. Password is hashed using bcrypt

**Database Table:** `admin_registrations`
- Stores: `id`, `email`, `hashed_password`, `full_name`, `created_at`

---

### 3.3 USER PORTAL LOGIN

#### Step 1: User Enters Credentials
**File:** `frontend/src/components/auth/Login.js`

**Location in Code:**
- Lines 915-926: `handleLogin()` function

**Form Submission:**
```javascript
await login(email, password);  // Calls AuthContext
navigate('/for-you');
```

#### Step 2: Frontend Calls AuthContext Login
**File:** `frontend/src/context/AuthContext.js`

**Location in Code:**
- Lines 55-98: `login()` function

**API Call:**
```javascript
const response = await fetch(`${API_CONFIG.BASE_URL}/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, password }),
});
```

#### Step 3: Backend Validates Login
**File:** `backend/app/main.py`

**Location in Code:**
- Lines 196-211: `login_user()` endpoint

**Endpoint:** `POST /auth/login`

**What Happens:**
1. Finds user by email:
   ```python
   user = await crud.get_user_by_email(db, credentials.email)
   ```
2. Verifies password:
   ```python
   bcrypt.checkpw(password_bytes, user.hashed_password.encode("utf-8"))
   ```
3. Returns user data if valid

#### Step 4: Frontend Stores User Session
- User data stored in localStorage
- User redirected to dashboard

---

### 3.4 ADMIN PORTAL LOGIN

**File:** `admin/src/components/auth/Login.js`

**Location in Code:**
- Lines 69-81: `handleLogin()` function

**API Call:**
```javascript
await login(email, password);  // Uses AuthContext
```

**Backend Endpoint:** `POST /admin/login` (Lines 304-325 in `main.py`)

**Process:** Same as user login but uses `admin_registrations` table

---

## 4. USER PORTAL FUNCTIONALITIES

### 4.1 ASSET MANAGEMENT

#### 4.1.1 Viewing Assets

**Frontend Component:** `frontend/src/components/assets/Assets.js`

**Location in Code:**
- Lines 102-129: `useEffect` hook that loads assets

**API Call:**
```javascript
const res = await listAssets(user?.email);
```

**Service File:** `frontend/src/services/assetsApi.js`

**Location in Code:**
- Lines 37-55: `listAssets()` function

**Backend Request:**
```javascript
const url = `${API_URL}/assets?user_email=${encodeURIComponent(userEmail)}`;
const res = await fetch(url);
```

**Backend Endpoint:** `GET /assets` (Lines 97-106 in `main.py`)

**What Happens:**
1. Backend receives request with `user_email` query parameter
2. Calls `crud.list_assets(db, status, user_email)`
3. Queries `assets` table filtered by email
4. Returns array of assets

**Database Query:**
```python
# In crud.py
query = select(models.Asset)
if user_email:
    query = query.where(models.Asset.email == user_email)
```

**Database Table:** `assets`
- Columns: `id`, `email_id`, `asset_type`, `location`, `description`, `status`, `assigned_date`, `return_date`
- Foreign Key: `email_id` references `users(email)`

---

#### 4.1.2 Creating an Asset

**Frontend Component:** `frontend/src/components/assets/Assets.js`

**Location in Code:**
- Lines 131-180: `add()` function

**User Action:**
1. User fills form: Type (Laptop/Charger/NetworkIssue), Location (WFH/WFO), Description
2. Email is auto-populated from logged-in user

**API Call:**
```javascript
const a = {
  email: assetEmail,
  type: assetType,
  location: assetLocation,
  status: "active",
  description: assetDescription,
};
await addAsset(a);
```

**Service File:** `frontend/src/services/assetsApi.js`

**Location in Code:**
- Lines 57-79: `addAsset()` function

**Backend Request:**
```javascript
const res = await fetch(`${API_URL}/assets`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(toSend),
});
```

**Backend Endpoint:** `POST /assets` (Lines 108-137 in `main.py`)

**What Happens:**
1. Receives asset data in request body
2. Validates data using Pydantic schema (`schemas.AssetCreate`)
3. Calls `crud.create_asset(db, asset_in)`
4. Creates record in `assets` table
5. **BIDIRECTIONAL SYNC:** Also creates entry in `admin_assets` table (Lines 116-132)
6. Returns created asset

**Database Operation:**
```python
# In crud.py
asset = models.Asset(
    email=asset_in.email,
    type=asset_in.type,
    location=asset_in.location,
    status=asset_in.status,
    description=asset_in.description,
    assigned_date=datetime.utcnow()
)
session.add(asset)
await session.commit()
```

**Bidirectional Sync:**
After creating asset, backend automatically creates `admin_asset` entry:
```python
admin_asset_data = schemas.AdminAssetCreate(
    id=created.id,
    email=created.email,
    type=created.type,
    location=created.location,
    ...
)
await crud.create_admin_asset(db, admin_asset_data)
```

**Database Tables:**
- `assets`: User's asset record
- `admin_assets`: Admin-visible copy (for admin portal)

---

#### 4.1.3 Updating an Asset

**Frontend Component:** `frontend/src/components/assets/Assets.js`

**Location in Code:**
- User clicks edit, modifies fields, clicks save

**API Call:**
```javascript
await updateAsset(id, patch);
```

**Service File:** `frontend/src/services/assetsApi.js`

**Location in Code:**
- Lines 88-107: `updateAsset()` function

**Backend Endpoint:** `PUT /assets/{asset_id}` (Lines 146-151 in `main.py`)

**What Happens:**
1. Updates `assets` table
2. Does NOT automatically sync to `admin_assets` (admin must update separately)

---

#### 4.1.4 Deleting an Asset

**Frontend Component:** `frontend/src/components/assets/Assets.js`

**API Call:**
```javascript
await deleteAsset(id);
```

**Backend Endpoint:** `DELETE /assets/{asset_id}` (Lines 153-158 in `main.py`)

**What Happens:**
- Deletes from `assets` table
- Foreign key constraint may cascade delete from `admin_assets` if configured

---

### 4.2 PROJECT MANAGEMENT

#### 4.2.1 Viewing Projects

**Frontend Component:** `frontend/src/components/projects/ProjectList.js`

**Location in Code:**
- Lines 88-95: `loadProjects()` function

**API Call:**
```javascript
const data = await listProjects();
```

**Service File:** `frontend/src/services/mockApi.js`

**Note:** Currently uses mock API (localStorage). To connect to backend:
- Use endpoint: `GET /projects?user_email={email}`

**Backend Endpoint:** `GET /projects` (Lines 502-512 in `main.py`)

**What Happens:**
1. Can filter by `user_email` (checks if user is in `leads` or `team_members`)
2. Returns all projects where user is a lead or team member

**Database Table:** `projects`
- Columns: `id`, `name`, `project_key`, `project_type`, `leads` (comma-separated emails), `team_members` (comma-separated emails), `description`, `created_at`, `updated_at`

---

#### 4.2.2 Creating a Project

**Frontend Component:** `frontend/src/components/projects/ProjectList.js`

**Location in Code:**
- Lines 97-121: `createProject()` function

**User Action:**
1. User enters: Name, Key, Type, Leads (comma-separated emails)
2. Clicks "Create Project"

**API Call:**
```javascript
await addProject(p);
```

**Backend Endpoint:** `POST /projects` (Lines 514-524 in `main.py`)

**What Happens:**
1. Receives project data
2. Creates record in `projects` table
3. Returns created project

**Database Operation:**
```python
project = models.Project(
    name=project_in.name,
    project_key=project_in.project_key,
    project_type=project_in.project_type,
    leads=", ".join(project_in.leads) if isinstance(project_in.leads, list) else project_in.leads,
    team_members=", ".join(project_in.team_members) if isinstance(project_in.team_members, list) else project_in.team_members,
    description=project_in.description
)
session.add(project)
await session.commit()
```

---

### 4.3 TICKET/ISSUE MANAGEMENT

#### 4.3.1 Creating a Ticket

**Frontend Component:** `frontend/src/components/issues/IssueCreate.js`

**User Action:**
1. User fills form: Title, Description, Status, Priority, Assignee, Reporter, Start Date, Due Date
2. Clicks "Create"

**API Call:**
```javascript
const response = await fetch('http://localhost:8000/tickets?epic_id=1&project_id=1&user_name=user@email.com', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: userId,
    title: title,
    description: description,
    status: 'Open',
    priority: 'Medium',
    assignee: assignee,
    reporter: reporter,
    start_date: startDate,
    due_date: dueDate
  }),
});
```

**Backend Endpoint:** `POST /tickets` (Lines 397-438 in `main.py`)

**Query Parameters:**
- `epic_id`: Optional epic ID
- `project_id`: Optional project ID
- `user_name`: User email (for admin portal visibility)

**What Happens:**
1. Creates ticket in `tickets` table
2. **BIDIRECTIONAL SYNC:** Automatically creates entry in `admin_tickets` table (Lines 405-433)
3. Gets project title if `project_id` provided
4. Creates `admin_ticket` with `project_title` and `user_name` for admin visibility

**Database Tables:**
- `tickets`: User's ticket record
  - Columns: `id`, `user_id`, `title`, `description`, `status`, `priority`, `assignee`, `reporter`, `start_date`, `due_date`, `ticket_code`, `created_at`, `updated_at`
- `admin_tickets`: Admin-visible copy
  - Additional columns: `ticket_id` (FK to tickets), `project_title`, `user_name`, `epic_id`, `project_id`

**Ticket Code Generation:**
- Format: `FL####V` (e.g., FL0001V)
- Generated automatically in `crud.py` using `_apply_ticket_code()`

---

#### 4.3.2 Viewing Tickets

**Frontend Component:** `frontend/src/components/boards/KanbanBoard.js`

**API Call:**
```javascript
const response = await fetch(`http://localhost:8000/tickets?user_id=${userId}`);
```

**Backend Endpoint:** `GET /tickets` (Lines 385-395 in `main.py`)

**Query Parameters:**
- `user_id`: Filter by user ID
- `status`: Filter by status

**What Happens:**
- Returns tickets from `tickets` table filtered by user_id

---

#### 4.3.3 Updating a Ticket

**Frontend Component:** `frontend/src/components/boards/KanbanBoard.js`

**API Call:**
```javascript
await fetch(`http://localhost:8000/tickets/${ticketId}`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(updatedFields),
});
```

**Backend Endpoint:** `PUT /tickets/{ticket_id}` (Lines 448-474 in `main.py`)

**What Happens:**
1. Updates `tickets` table
2. **BIDIRECTIONAL SYNC:** Also updates corresponding `admin_tickets` entry (Lines 456-472)

---

#### 4.3.4 Deleting a Ticket

**Backend Endpoint:** `DELETE /tickets/{ticket_id}` (Lines 476-499 in `main.py`)

**What Happens:**
1. Deletes from `tickets` table
2. **BIDIRECTIONAL SYNC:** Also deletes corresponding `admin_tickets` entry (Lines 485-492)

---

### 4.4 EPIC MANAGEMENT

#### 4.4.1 Creating an Epic

**Backend Endpoint:** `POST /epics` (Lines 563-595 in `main.py`)

**Query Parameters:**
- `user_name`: User email (for admin portal visibility)

**What Happens:**
1. Creates epic in `epics` table
2. **BIDIRECTIONAL SYNC:** Automatically creates entry in `admin_epics` table (Lines 571-590)

**Database Tables:**
- `epics`: User's epic record
  - Columns: `id`, `project_id`, `name`, `created_at`, `updated_at`
- `admin_epics`: Admin-visible copy
  - Additional columns: `epic_id` (FK to epics), `project_title`, `user_name`, `project_id`

---

### 4.5 USER PROFILE MANAGEMENT

#### 4.5.1 Viewing Profile

**Frontend Component:** `frontend/src/components/users/Users.js`

**API Call:**
```javascript
const profile = await getUserProfile(user.email);
```

**Service File:** `frontend/src/services/userManagementApi.js`

**Location in Code:**
- Lines 77-93: `getUserProfile()` function

**Backend Endpoint:** `GET /user-profiles/email/{email}` (Lines 764-770 in `main.py`)

**Database Table:** `user_profile`
- Columns: `user_id`, `full_name`, `email`, `mobile_number`, `role`, `department`, `date_of_birth`, `user_status`, `created_at`, `updated_at`

---

#### 4.5.2 Creating/Updating Profile

**Service File:** `frontend/src/services/userManagementApi.js`

**Location in Code:**
- Lines 10-70: `saveUserProfile()` function

**What Happens:**
1. Checks if profile exists by email
2. If exists: Updates via `PUT /user-profiles/{user_id}`
3. If not exists: Creates via `POST /user-profiles`

**Backend Endpoints:**
- `POST /user-profiles` (Lines 772-821 in `main.py`)
- `PUT /user-profiles/{user_id}` (Lines 823-858 in `main.py`)

**Bidirectional Sync:**
- When creating/updating `user_profile`, backend automatically syncs to `users_management` table (Lines 788-813, 832-851)

**Database Tables:**
- `user_profile`: User portal profile data
- `users_management`: Admin portal user data (synced automatically)

---

## 5. ADMIN PORTAL FUNCTIONALITIES

### 5.1 ADMIN ASSET MANAGEMENT

#### 5.1.1 Viewing All Assets

**Frontend Component:** `admin/src/components/assets/Assets.js`

**API Call:**
```javascript
const response = await fetch('http://localhost:8000/admin/assets');
```

**Backend Endpoint:** `GET /admin/assets` (Lines 328-338 in `main.py`)

**What Happens:**
- Returns all assets from `admin_assets` table
- Shows assets from all users

**Database Table:** `admin_assets`
- Columns: `admin_asset_id`, `id` (FK to assets), `email_id`, `asset_type`, `location`, `description`, `status`, `assigned_date`, `return_date`, `actions`

---

#### 5.1.2 Updating Admin Asset

**Backend Endpoint:** `PUT /admin/assets/{admin_asset_id}` (Lines 348-374 in `main.py`)

**What Happens:**
1. Updates `admin_assets` table
2. **BIDIRECTIONAL SYNC:** Also updates corresponding `assets` table (Lines 357-367)

**This is bidirectional:** Admin edits sync to user's asset record

---

#### 5.1.3 Deleting Admin Asset

**Backend Endpoint:** `DELETE /admin/assets/{admin_asset_id}` (Lines 376-382 in `main.py`)

**What Happens:**
- Deletes from `admin_assets` table
- May cascade delete from `assets` if foreign key constraint configured

---

### 5.2 ADMIN PROJECT MANAGEMENT

**Frontend Component:** `admin/src/components/projects/ProjectList.js`

**API Calls:**
- `GET /projects`: List all projects
- `POST /projects`: Create project
- `PUT /projects/{project_id}`: Update project
- `DELETE /projects/{project_id}`: Delete project

**Backend Endpoints:** Same as user portal (Lines 502-548 in `main.py`)

**Difference:** Admin can see ALL projects, not filtered by user

---

### 5.3 ADMIN TICKET MANAGEMENT

#### 5.3.1 Viewing All Tickets

**Frontend Component:** `admin/src/components/boards/KanbanBoard.js`

**API Call:**
```javascript
const response = await fetch('http://localhost:8000/admin/tickets');
```

**Backend Endpoint:** `GET /admin/tickets` (Lines 943-953 in `main.py`)

**Query Parameters:**
- `project_id`: Filter by project
- `epic_id`: Filter by epic

**What Happens:**
- Returns all tickets from `admin_tickets` table
- Shows tickets from all users with `project_title` and `user_name` for easy identification

---

#### 5.3.2 Creating Ticket (Admin Portal)

**Frontend Component:** `admin/src/components/boards/KanbanBoard.js`

**Location in Code:**
- Lines 1325-1418: `createIssueAPI()` function

**What Happens:**
1. Gets or creates user ID for logged-in admin
2. Makes POST request to `/tickets` with query parameters:
   - `epic_id`, `project_id`, `user_name`
3. Backend creates ticket in `tickets` table
4. Backend automatically creates `admin_ticket` entry

---

#### 5.3.3 Updating Admin Ticket

**Backend Endpoint:** `PUT /admin/tickets/{admin_ticket_id}` (Lines 963-992 in `main.py`)

**What Happens:**
1. Updates `admin_tickets` table
2. **BIDIRECTIONAL SYNC:** Also updates corresponding `tickets` table (Lines 972-985)

---

#### 5.3.4 Deleting Admin Ticket

**Backend Endpoint:** `DELETE /admin/tickets/{admin_ticket_id}` (Lines 994-1021 in `main.py`)

**What Happens:**
1. Deletes from `admin_tickets` table
2. **BIDIRECTIONAL SYNC:** Also deletes corresponding `tickets` table entry (Lines 1008-1014)

---

### 5.4 ADMIN EPIC MANAGEMENT

**Backend Endpoints:**
- `GET /admin/epics` (Lines 906-916)
- `PUT /admin/epics/{admin_epic_id}` (Lines 926-932)
- `DELETE /admin/epics/{admin_epic_id}` (Lines 934-940)

**What Happens:**
- Admin can view all epics from all users
- Updates/deletes sync bidirectionally with `epics` table

---

### 5.5 USER MANAGEMENT (Admin Portal)

#### 5.5.1 Viewing All Users

**Frontend Component:** `admin/src/components/users/Users.js`

**API Call:**
```javascript
const response = await fetch('http://localhost:8000/users-management');
```

**Backend Endpoint:** `GET /users-management` (Lines 623-633 in `main.py`)

**Database Table:** `users_management`
- Columns: `id`, `first_name`, `last_name`, `email`, `role`, `department`, `tickets_issued`, `tickets_resolved`, `active`, `language`, `mobile_number`, `date_format`, `password_reset_needed`, `profile_file_name`, `profile_file_size`, `created_at`, `updated_at`

---

#### 5.5.2 Creating User (Admin Portal)

**Backend Endpoint:** `POST /users-management` (Lines 643-678 in `main.py`)

**What Happens:**
1. Creates user in `users_management` table
2. **BIDIRECTIONAL SYNC:** Automatically creates entry in `user_profile` table (Lines 656-670)

---

#### 5.5.3 Updating User (Admin Portal)

**Backend Endpoint:** `PUT /users-management/{user_id}` (Lines 680-704 in `main.py`)

**What Happens:**
1. Updates `users_management` table
2. **BIDIRECTIONAL SYNC:** Also updates corresponding `user_profile` entry (Lines 687-702)

---

#### 5.5.4 Deleting User (Admin Portal)

**Backend Endpoint:** `DELETE /users-management/{user_id}` (Lines 706-749 in `main.py`)

**What Happens:**
1. Deletes from `users_management` table
2. **BIDIRECTIONAL SYNC:** Also deletes from `user_profile` table (Lines 724-731)
3. **BIDIRECTIONAL SYNC:** Also deletes from `users` table (authentication) (Lines 733-741)

**Complete Sync:** User deleted from ALL tables (users_management, user_profile, users)

---

## 6. DATABASE SCHEMA & DATA FLOW

### 6.1 Key Tables

#### Authentication Tables
1. **`users`**: User portal authentication
   - `id`, `email`, `hashed_password`, `full_name`, `created_at`

2. **`admin_registrations`**: Admin portal authentication
   - `id`, `email`, `hashed_password`, `full_name`, `created_at`

#### Profile Tables
3. **`user_profile`**: User portal profile data
   - `user_id`, `full_name`, `email`, `mobile_number`, `role`, `department`, `date_of_birth`, `user_status`, `created_at`, `updated_at`

4. **`users_management`**: Admin portal user data
   - `id`, `first_name`, `last_name`, `email`, `role`, `department`, `tickets_issued`, `tickets_resolved`, `active`, `language`, `mobile_number`, `date_format`, `password_reset_needed`, `profile_file_name`, `profile_file_size`, `created_at`, `updated_at`

#### Asset Tables
5. **`assets`**: User portal assets
   - `id`, `email_id` (FK to users.email), `asset_type`, `location`, `description`, `status`, `assigned_date`, `return_date`

6. **`admin_assets`**: Admin portal asset management
   - `admin_asset_id`, `id` (FK to assets.id), `email_id` (FK to users.email), `asset_type`, `location`, `description`, `status`, `assigned_date`, `return_date`, `actions`

#### Project Tables
7. **`projects`**: All projects
   - `id`, `name`, `project_key`, `project_type`, `leads` (comma-separated emails), `team_members` (comma-separated emails), `description`, `created_at`, `updated_at`

#### Epic Tables
8. **`epics`**: User portal epics
   - `id`, `project_id`, `name`, `created_at`, `updated_at`

9. **`admin_epics`**: Admin portal epics
   - `admin_epic_id`, `epic_id` (FK to epics.id), `project_id`, `project_title`, `user_name`, `name`, `created_at`, `updated_at`

#### Ticket Tables
10. **`tickets`**: User portal tickets
    - `id`, `user_id` (reference to users.id), `title`, `description`, `status`, `priority`, `assignee`, `reporter`, `start_date`, `due_date`, `ticket_code`, `created_at`, `updated_at`

11. **`admin_tickets`**: Admin portal tickets
    - `admin_ticket_id`, `ticket_id` (FK to tickets.id), `ticket_code`, `epic_id`, `project_id`, `project_title`, `user_name`, `title`, `description`, `status`, `priority`, `assignee`, `reporter`, `start_date`, `due_date`, `created_at`, `updated_at`

### 6.2 Foreign Key Relationships

```
users.email ← assets.email_id
users.email ← admin_assets.email_id
users.id ← tickets.user_id (reference, no FK constraint)
assets.id ← admin_assets.id
epics.id ← admin_epics.epic_id (reference)
tickets.id ← admin_tickets.ticket_id (reference)
projects.id ← epics.project_id (reference)
```

### 6.3 Data Flow Diagrams

#### Asset Creation Flow (User Portal)
```
User fills form → Frontend (Assets.js)
  → assetsApi.addAsset()
    → POST /assets
      → Backend (main.py: create_asset)
        → crud.create_asset()
          → INSERT INTO assets
          → INSERT INTO admin_assets (automatic sync)
            → Response to frontend
```

#### Ticket Creation Flow (User Portal)
```
User fills form → Frontend (IssueCreate.js)
  → POST /tickets?epic_id=X&project_id=Y&user_name=email
    → Backend (main.py: create_ticket)
      → crud.create_ticket()
        → INSERT INTO tickets
        → Generate ticket_code (FL####V)
        → INSERT INTO admin_tickets (automatic sync)
          → Response to frontend
```

#### Bidirectional Sync Flow (Admin Updates Asset)
```
Admin edits asset → Frontend (admin/Assets.js)
  → PUT /admin/assets/{admin_asset_id}
    → Backend (main.py: update_admin_asset)
      → crud.update_admin_asset()
        → UPDATE admin_assets
        → UPDATE assets (automatic sync)
          → Response to frontend
```

---

## 7. API ENDPOINTS REFERENCE

### 7.1 Authentication Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| POST | `/auth/register` | User registration | `{email, password, full_name}` | `{id, email, full_name}` |
| POST | `/auth/login` | User login | `{email, password}` | `{id, email, full_name}` |
| POST | `/admin/register` | Admin registration | `{email, password, full_name}` | `{id, email, full_name}` |
| POST | `/admin/login` | Admin login | `{email, password}` | `{id, email, full_name}` |

### 7.2 Asset Endpoints

| Method | Endpoint | Description | Query Params | Request Body |
|--------|----------|-------------|--------------|--------------|
| GET | `/assets` | List assets | `status`, `user_email` | - |
| POST | `/assets` | Create asset | - | `{email, type, location, status, description}` |
| GET | `/assets/{asset_id}` | Get asset | - | - |
| PUT | `/assets/{asset_id}` | Update asset | - | `{email, type, location, status, description}` |
| DELETE | `/assets/{asset_id}` | Delete asset | - | - |
| GET | `/admin/assets` | List all admin assets | - | - |
| GET | `/admin/assets/{admin_asset_id}` | Get admin asset | - | - |
| PUT | `/admin/assets/{admin_asset_id}` | Update admin asset | - | `{email, type, location, status, description}` |
| DELETE | `/admin/assets/{admin_asset_id}` | Delete admin asset | - | - |

### 7.3 Project Endpoints

| Method | Endpoint | Description | Query Params | Request Body |
|--------|----------|-------------|--------------|--------------|
| GET | `/projects` | List projects | `user_email` | - |
| POST | `/projects` | Create project | - | `{name, project_key, project_type, leads, team_members, description}` |
| GET | `/projects/{project_id}` | Get project | - | - |
| PUT | `/projects/{project_id}` | Update project | - | `{name, project_key, project_type, leads, team_members, description}` |
| DELETE | `/projects/{project_id}` | Delete project | - | - |

### 7.4 Ticket Endpoints

| Method | Endpoint | Description | Query Params | Request Body |
|--------|----------|-------------|--------------|--------------|
| GET | `/tickets` | List tickets | `user_id`, `status` | - |
| POST | `/tickets` | Create ticket | `epic_id`, `project_id`, `user_name` | `{user_id, title, description, status, priority, assignee, reporter, start_date, due_date}` |
| GET | `/tickets/{ticket_id}` | Get ticket | - | - |
| PUT | `/tickets/{ticket_id}` | Update ticket | - | `{title, description, status, priority, assignee, reporter, start_date, due_date}` |
| DELETE | `/tickets/{ticket_id}` | Delete ticket | - | - |
| GET | `/admin/tickets` | List all admin tickets | `project_id`, `epic_id` | - |
| GET | `/admin/tickets/{admin_ticket_id}` | Get admin ticket | - | - |
| PUT | `/admin/tickets/{admin_ticket_id}` | Update admin ticket | - | `{title, description, status, priority, assignee, reporter, start_date, due_date}` |
| DELETE | `/admin/tickets/{admin_ticket_id}` | Delete admin ticket | - | - |

### 7.5 Epic Endpoints

| Method | Endpoint | Description | Query Params | Request Body |
|--------|----------|-------------|--------------|--------------|
| GET | `/epics` | List epics | `project_id` | - |
| POST | `/epics` | Create epic | `user_name` | `{project_id, name}` |
| DELETE | `/epics/{epic_id}` | Delete epic | - | - |
| GET | `/admin/epics` | List all admin epics | `project_id` | - |
| GET | `/admin/epics/{admin_epic_id}` | Get admin epic | - | - |
| PUT | `/admin/epics/{admin_epic_id}` | Update admin epic | - | `{name}` |
| DELETE | `/admin/epics/{admin_epic_id}` | Delete admin epic | - | - |

### 7.6 User Management Endpoints

| Method | Endpoint | Description | Query Params | Request Body |
|--------|----------|-------------|--------------|--------------|
| GET | `/users/` | List users | - | - |
| GET | `/users/{user_id}` | Get user | - | - |
| POST | `/users/` | Create user | - | `{full_name, email, role, department, mobile_number, date_of_birth, user_status}` |
| PUT | `/users/{user_id}` | Update user | - | `{full_name, role, department, mobile_number, user_status}` |
| DELETE | `/users/{user_id}` | Delete user | - | - |
| GET | `/users-by-email/{email}` | Get user by email | - | - |
| POST | `/users-simple` | Create simple user | - | `{email, name}` |
| GET | `/users-management` | List all users (admin) | - | - |
| GET | `/users-management/email/{email}` | Get user by email (admin) | - | - |
| POST | `/users-management` | Create user (admin) | - | `{first_name, last_name, email, role, department, active, language, mobile_number, date_format}` |
| PUT | `/users-management/{user_id}` | Update user (admin) | - | `{first_name, last_name, email, role, department, active, mobile_number}` |
| DELETE | `/users-management/{user_id}` | Delete user (admin) | - | - |
| GET | `/user-profiles` | List all user profiles | - | - |
| GET | `/user-profiles/email/{email}` | Get user profile by email | - | - |
| POST | `/user-profiles` | Create user profile | - | `{full_name, email, role, department, mobile_number, date_of_birth, user_status}` |
| PUT | `/user-profiles/{user_id}` | Update user profile | - | `{full_name, role, department, mobile_number, user_status}` |
| DELETE | `/user-profiles/{user_id}` | Delete user profile | - | - |

---

## 8. BIDIRECTIONAL SYNC MECHANISMS

### 8.1 Asset Sync

**User Portal → Admin Portal:**
- When user creates asset → Automatically creates `admin_asset` entry
- Location: `backend/app/main.py` Lines 116-132

**Admin Portal → User Portal:**
- When admin updates asset → Automatically updates `assets` table
- Location: `backend/app/main.py` Lines 357-367

### 8.2 Ticket Sync

**User Portal → Admin Portal:**
- When user creates ticket → Automatically creates `admin_ticket` entry
- Location: `backend/app/main.py` Lines 405-433

**Admin Portal → User Portal:**
- When admin updates ticket → Automatically updates `tickets` table
- Location: `backend/app/main.py` Lines 972-985
- When admin deletes ticket → Automatically deletes from `tickets` table
- Location: `backend/app/main.py` Lines 1008-1014

### 8.3 Epic Sync

**User Portal → Admin Portal:**
- When user creates epic → Automatically creates `admin_epic` entry
- Location: `backend/app/main.py` Lines 571-590

**Admin Portal → User Portal:**
- When admin deletes epic → Automatically deletes from `epics` table
- Location: `backend/app/main.py` Lines 606-613

### 8.4 User Profile Sync

**User Portal → Admin Portal:**
- When user creates/updates profile → Automatically syncs to `users_management` table
- Location: `backend/app/main.py` Lines 788-813, 832-851

**Admin Portal → User Portal:**
- When admin creates/updates user → Automatically syncs to `user_profile` table
- Location: `backend/app/main.py` Lines 656-670, 687-702

**Complete Deletion Sync:**
- When admin deletes user → Deletes from ALL tables: `users_management`, `user_profile`, `users`
- Location: `backend/app/main.py` Lines 717-743

---

## 9. KEY CONCEPTS EXPLAINED

### 9.1 Why Two Tables for Same Data?

**Example: Assets**
- `assets` table: User portal view (user sees only their assets)
- `admin_assets` table: Admin portal view (admin sees all users' assets)

**Benefits:**
1. **Performance:** Admin queries don't need complex joins
2. **Data Denormalization:** `admin_assets` includes `project_title` and `user_name` for easy display
3. **Separation of Concerns:** User and admin portals have different data needs

### 9.2 How Bidirectional Sync Works

**When User Creates Asset:**
1. Frontend calls `POST /assets`
2. Backend creates record in `assets` table
3. Backend automatically creates record in `admin_assets` table
4. Both tables stay in sync

**When Admin Updates Asset:**
1. Frontend calls `PUT /admin/assets/{admin_asset_id}`
2. Backend updates `admin_assets` table
3. Backend automatically updates corresponding `assets` table
4. Both tables stay in sync

### 9.3 Ticket Code Generation

**Format:** `FL####V` (e.g., FL0001V, FL0002V)

**How it Works:**
1. Ticket created in `tickets` table
2. Backend function `_apply_ticket_code()` generates code
3. Code stored in `ticket_code` column
4. Same code synced to `admin_tickets.ticket_code`

**Location:** `backend/app/crud.py` (function `_apply_ticket_code()`)

### 9.4 User ID Resolution

**Problem:** Tickets need `user_id` but frontend only has email

**Solution:**
1. Frontend calls `GET /users-by-email/{email}` to get user ID
2. If user doesn't exist, calls `POST /users-simple` to create user
3. Uses returned `user_id` when creating ticket

**Location:** `admin/src/components/boards/KanbanBoard.js` Lines 1334-1369

---

## 10. COMMON WORKFLOWS

### 10.1 Complete User Registration to Asset Creation

1. **User registers:**
   - Frontend: `Login.js` → `AuthContext.register()`
   - Backend: `POST /auth/register`
   - Database: INSERT INTO `users`

2. **User logs in:**
   - Frontend: `Login.js` → `AuthContext.login()`
   - Backend: `POST /auth/login`
   - Frontend: Stores user in localStorage

3. **User creates profile:**
   - Frontend: `Users.js` → `saveUserProfile()`
   - Backend: `POST /user-profiles`
   - Database: INSERT INTO `user_profile`
   - Backend: Auto-syncs to `users_management`

4. **User creates asset:**
   - Frontend: `Assets.js` → `addAsset()`
   - Backend: `POST /assets`
   - Database: INSERT INTO `assets`
   - Backend: Auto-syncs to `admin_assets`

### 10.2 Complete Ticket Creation Flow

1. **User creates project:**
   - Frontend: `ProjectList.js` → `addProject()`
   - Backend: `POST /projects`
   - Database: INSERT INTO `projects`

2. **User creates epic:**
   - Frontend: `Backlog.js` or `KanbanBoard.js`
   - Backend: `POST /epics?user_name=email`
   - Database: INSERT INTO `epics`
   - Backend: Auto-syncs to `admin_epics`

3. **User creates ticket:**
   - Frontend: `IssueCreate.js` or `KanbanBoard.js`
   - Backend: `POST /tickets?epic_id=X&project_id=Y&user_name=email`
   - Database: INSERT INTO `tickets`
   - Backend: Generates `ticket_code` (FL####V)
   - Backend: Auto-syncs to `admin_tickets` with `project_title` and `user_name`

4. **Admin views ticket:**
   - Frontend: `admin/src/components/boards/KanbanBoard.js`
   - Backend: `GET /admin/tickets`
   - Database: SELECT FROM `admin_tickets`
   - Admin sees ticket with project title and user name

---

## 11. TROUBLESHOOTING GUIDE

### 11.1 Common Issues

**Issue: "Cannot connect to server"**
- **Cause:** Backend not running
- **Solution:** Start backend: `cd backend && python -m uvicorn app.main:app --reload`

**Issue: "User not found"**
- **Cause:** User not registered or email mismatch
- **Solution:** Check `users` table, ensure user exists

**Issue: "Asset not syncing to admin portal"**
- **Cause:** Backend sync code may have failed (non-critical error)
- **Solution:** Check backend logs, manually create `admin_asset` entry if needed

**Issue: "Ticket code not generated"**
- **Cause:** `_apply_ticket_code()` function may have failed
- **Solution:** Check `tickets.ticket_code` column, may be NULL

### 11.2 Database Connection Issues

**Check Database:**
```sql
-- Verify tables exist
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- Check users
SELECT * FROM users LIMIT 5;

-- Check assets
SELECT * FROM assets LIMIT 5;

-- Check tickets
SELECT * FROM tickets LIMIT 5;
```

---

## 12. FILE LOCATION REFERENCE

### Frontend Files

| Functionality | User Portal File | Admin Portal File |
|---------------|-------------------|-------------------|
| Login | `frontend/src/components/auth/Login.js` | `admin/src/components/auth/Login.js` |
| Registration | `frontend/src/components/auth/Login.js` (embedded) | `admin/src/components/auth/Registration.js` |
| Assets | `frontend/src/components/assets/Assets.js` | `admin/src/components/assets/Assets.js` |
| Projects | `frontend/src/components/projects/ProjectList.js` | `admin/src/components/projects/ProjectList.js` |
| Tickets | `frontend/src/components/issues/IssueCreate.js` | `admin/src/components/boards/KanbanBoard.js` |
| Users | `frontend/src/components/users/Users.js` | `admin/src/components/users/Users.js` |
| Auth Context | `frontend/src/context/AuthContext.js` | `admin/src/context/AuthContext.js` |
| API Config | `frontend/src/config/api.js` | - |

### Backend Files

| Functionality | File | Key Sections |
|---------------|------|--------------|
| All Routes | `backend/app/main.py` | All endpoints defined here |
| Database Models | `backend/app/models.py` | SQLAlchemy table definitions |
| Request/Response Schemas | `backend/app/schemas.py` | Pydantic validation schemas |
| Database Operations | `backend/app/crud.py` | All CREATE, READ, UPDATE, DELETE functions |
| Database Connection | `backend/app/database.py` | PostgreSQL connection setup |
| Database Schema | `ticketflow/DATABASE_SCHEMA.sql` | Complete SQL schema |

### Service Files (Frontend API Calls)

| Service | File |
|---------|------|
| Assets API | `frontend/src/services/assetsApi.js` |
| User API | `frontend/src/services/userApi.js` |
| User Management API | `frontend/src/services/userManagementApi.js` |
| Mock API (Projects) | `frontend/src/services/mockApi.js` |

---

## 13. SUMMARY

### Key Takeaways

1. **Two Portals:** User Portal and Admin Portal share same backend but have different views
2. **Bidirectional Sync:** Changes in one portal automatically sync to the other
3. **Database Design:** Separate tables for user/admin views enable better performance and separation
4. **Authentication:** Separate tables for user and admin authentication
5. **Ticket System:** Tickets sync between portals with project title and user name for admin visibility
6. **Asset System:** Assets sync bidirectionally between user and admin portals

### Data Flow Summary

```
User Action → Frontend Component
  → Service/API File
    → HTTP Request (fetch)
      → Backend Endpoint (FastAPI)
        → CRUD Function
          → Database Operation (SQLAlchemy)
            → Response
              → Frontend Update
```

### Sync Summary

- **Assets:** `assets` ↔ `admin_assets`
- **Tickets:** `tickets` ↔ `admin_tickets`
- **Epics:** `epics` ↔ `admin_epics`
- **User Profiles:** `user_profile` ↔ `users_management`

---

## END OF DOCUMENTATION

This documentation covers every functionality from registration to the last feature in the FlowTrack project. Each step includes:
- Frontend file locations and code references
- Backend endpoint locations and code references
- Database operations and table names
- Bidirectional sync mechanisms
- Complete data flow diagrams

For any questions or clarifications, refer to the specific file locations mentioned in each section.

