# AMU Cloud-Based Academic Resource Management System

## Phase 7: Process Modelling and Phase 8: Data Analysis

This revised version includes folder management and organization, student and teacher upload quotas, automatic approval of teacher uploads after validation, and administrator resource-management permissions.

### Confirmed system rules

| Feature                   | Agreed requirement                                                    |
| ------------------------- | --------------------------------------------------------------------- |
| Student storage quota     | 1 GB per student                                                      |
| Teacher storage quota     | 15 GB per teacher                                                     |
| Student uploads           | Allowed within the student's quota                                    |
| Teacher uploads           | Allowed within the teacher's quota                                    |
| Teacher resource approval | Automatically approved after validation and successful saving         |
| Administrator permissions | Create, edit, and remove resources                                    |
| Folder management         | Organize resources into folders and subfolders                        |
| Resource discovery        | Search and browse resources, including by folder and subject          |
| Cloud storage             | Check file size, file type, and remaining user quota before uploading |

The maximum individual file size and the overall cloud-provider capacity still need to be defined separately. A user's quota limits the storage they can consume; it does not guarantee that the overall cloud account has unlimited capacity.

# Phase 7: Process Modelling

## 7.1 Objective

Process modelling describes the activities performed by students, teachers, and administrators, the system's boundaries, and how information moves between system processes and data stores.

## 7.2 Activity Diagram — Uploading and Organizing Resources

This diagram covers login, folder selection or creation, upload validation, storage quota enforcement, and the different permissions of students, teachers, and administrators.

```mermaid

flowchart TD
    A([Start]) --> B[Open system and log in]
    B --> C{Credentials valid?}
    C -- No --> D[Display login error]
    D --> B
    C -- Yes --> E[Identify user role]
    E --> F[Check role permissions]

    F --> G{Choose activity}

    G -- Upload resource --> H[Enter resource details]
    H --> I[Select existing folder or create a folder]
    I --> J[Choose file or provide a link]
    J --> K[Validate file type, size and metadata]
    K --> L{Input valid?}
    L -- No --> M[Display validation error]
    M --> H
    L -- Yes --> N[Check user's remaining storage quota]
    N --> O{Enough quota and cloud capacity?}
    O -- No --> P[Display storage limit message]
    P --> Z([End])
    O -- Yes --> Q[Upload file to cloud storage]
    Q --> R{Upload successful?}
    R -- No --> S[Report upload failure]
    S --> Z
    R -- Yes --> T[Save resource metadata and folder reference]
    T --> U[Update storage usage]
    U --> V{Uploader role?}
    V -- Teacher --> W[Automatically approve resource]
    W --> X[Make resource available according to permissions]
    V -- Student --> Y[Apply student resource visibility policy]
    Y --> Z
    X --> Z

    G -- Manage folders --> AA[Create, rename, move or organize folders]
    AA --> AB[Validate folder permissions and parent folder]
    AB --> AC[Save folder changes]
    AC --> Z

    G -- Browse or search --> AD[Search resources or browse folders]
    AD --> AE[Check resource access permissions]
    AE --> AF[Display permitted resources]
    AF --> Z

    G -- Administrator management --> AG[Select resource]
    AG --> AH{Create, edit or remove?}
    AH -- Create --> AI[Enter and validate resource details]
    AI --> AJ[Save resource]
    AH -- Edit --> AK[Update resource or folder details]
    AK --> AL[Validate and save changes]
    AH -- Remove --> AM[Confirm removal]
    AM --> AN[Remove from availability and handle stored files]
    AJ --> Z
    AL --> Z
    AN --> Z

```

Notes for the report:

- Folder operations must check permissions so users cannot edit or delete another user's private folders.
- A folder may contain subfolders and resources. Moving a resource should update its folder reference without duplicating the stored file.
- Teacher uploads are automatically approved only after validation and successful saving.
- The visibility policy for student uploads needs a final decision. This diagram intentionally does not assume that student uploads receive automatic approval.
- Deleting a resource from the application and permanently deleting its cloud file are separate decisions. The system must handle both consistently.

## 7.3 Context Diagram

The context diagram shows the system as a single process and its interactions with external entities and supporting services.

```mermaid

flowchart LR
    ST[Student]
    TE[Teacher]
    AD[Administrator]
    AUTH[Authentication Service]
    CLOUD[Cloud Storage Service]

    SYS(("AMU Academic Resource Management System"))

    ST -->|Credentials, uploads, folder actions, search queries, download requests| SYS
    SYS -->|Upload status, quota information, folder listings, search results, accessible resources| ST

    TE -->|Credentials, uploads, folder actions, resource updates, search queries| SYS
    SYS -->|Upload status, quota information, folder listings, resource status, search results| TE

    AD -->|Resource creation, editing, removal and folder-management actions| SYS
    SYS -->|Resource records, folder information, storage usage and operation results| AD

    SYS -->|Authentication request| AUTH
    AUTH -->|Authentication result| SYS

    SYS -->|Store, retrieve and remove files| CLOUD
    CLOUD -->|Storage results, file references and retrieved files| SYS

```

### System boundary

Inside the system: user roles and permissions, resource metadata, upload validation, individual storage quotas, folder management, search, resource access, and resource administration.

Outside the system: the cloud storage provider and any external authentication provider, if one is used.

Moodle, SAMARTH-ERP, and the e-Library remain separate platforms. Direct integration with them is not assumed.

## 7.4 DFD Level 0 — Major Processes

The Level 0 Data Flow Diagram shows the major processes and the information exchanged with the system's data stores.

```mermaid

flowchart TB
    ST[Student]
    TE[Teacher]
    AD[Administrator]

    P1(("1.0 Authenticate User"))
    P2(("2.0 Manage Resources"))
    P3(("3.0 Manage Folders"))
    P4(("4.0 Search and Access Resources"))
    P5(("5.0 Manage Storage Quotas"))
    P6(("6.0 Administer Resources and Folders"))

    D1[("D1: Users and Roles")]
    D2[("D2: Departments and Subjects")]
    D3[("D3: Resource Metadata")]
    D4[("D4: Folders")]
    D5[("D5: Resource Versions and File References")]
    D6[("D6: Storage Quotas and Usage")]

    ST -->|Login credentials| P1
    TE -->|Login credentials| P1
    AD -->|Login credentials| P1
    P1 <--> D1
    P1 -->|Authentication result| ST
    P1 -->|Authentication result| TE
    P1 -->|Authentication result| AD

    ST -->|Resource upload and metadata| P2
    TE -->|Resource upload and metadata| P2
    P2 -->|Quota check request| P5
    P5 <--> D6
    P5 -->|Quota decision| P2
    P2 -->|Validated resource metadata| D3
    P2 -->|File reference and version| D5
    P2 -->|Upload result and approval status| ST
    P2 -->|Upload result and approval status| TE
    P2 <--> D2
    P2 <--> D4

    ST -->|Create or organize folders| P3
    TE -->|Create or organize folders| P3
    P3 <--> D4
    P3 -->|Folder operation result| ST
    P3 -->|Folder operation result| TE

    ST -->|Search or resource request| P4
    TE -->|Search or resource request| P4
    P4 -->|Read resource metadata| D3
    P4 -->|Read folder hierarchy| D4
    P4 -->|Read subject information| D2
    P4 -->|Read file references| D5
    P4 -->|Search results and permitted resources| ST
    P4 -->|Search results and permitted resources| TE

    AD -->|Create, edit, remove resources or manage folders| P6
    P6 <--> D3
    P6 <--> D4
    P6 <--> D5
    P6 -->|Resource and folder operation result| AD

```

### Process descriptions

| Process                              | Responsibility                                                                                                                                         |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1.0 Authenticate User                | Authenticates users and retrieves their role and permissions.                                                                                          |
| 2.0 Manage Resources                 | Validates uploads, checks quota availability, stores resource metadata and file references, and applies the appropriate approval or visibility policy. |
| 3.0 Manage Folders                   | Creates and organizes folders and subfolders, and moves resources between permitted folders.                                                           |
| 4.0 Search and Access Resources      | Searches resources, browses folders, and checks access permissions before providing resource access.                                                   |
| 5.0 Manage Storage Quotas            | Checks per-user quotas, records usage, and prevents uploads from exceeding available capacity.                                                         |
| 6.0 Administer Resources and Folders | Allows administrators to create, edit, and remove resources and perform authorized folder-management operations.                                       |

Storage quota rules: A student's allocation is 1 GB; a teacher's allocation is 15 GB. Uploads must pass both the user's quota check and the overall provider-capacity check.

The cloud storage provider is an external service. The actual file content resides there, while the database stores resource metadata, folder associations, version information, and file references.

## 7.5 DFD Level 1 — Manage Resources

This diagram expands process 2.0 to show validation, folder assignment, quota checking, file storage, metadata saving, and approval behaviour.

```mermaid

flowchart TB
    U[Student or Teacher]
    QP(("2.1 Validate Resource Input"))
    FP(("2.2 Validate Folder and Subject"))
    QC(("2.3 Check Storage Quota"))
    FS(("2.4 Store File in Cloud"))
    MD(("2.5 Save Resource Metadata"))
    VR(("2.6 Record Resource Version"))
    AP(("2.7 Apply Approval and Visibility Rules"))

    D1[("D1: Users and Roles")]
    D2[("D2: Subjects")]
    D3[("D3: Resource Metadata")]
    D4[("D4: Folders")]
    D5[("D5: Resource Versions and File References")]
    D6[("D6: Storage Quotas and Usage")]
    CS[("External Cloud Storage")]

    U -->|File or link, metadata, folder selection| QP
    QP -->|Invalid input and error details| U
    QP -->|Valid resource details| FP

    FP <--> D2
    FP <--> D4
    FP -->|Invalid folder or subject| U
    FP -->|Validated resource details| QC

    QC <--> D1
    QC <--> D6
    QC -->|Quota exceeded| U
    QC -->|Quota available| FS

    FS -->|Store uploaded file| CS
    CS -->|Storage confirmation and file reference| FS
    FS -->|Upload failure| U
    FS -->|File reference or external URL| MD

    MD -->|Save resource metadata| D3
    MD -->|Resource identifier and file reference| VR
    VR -->|Version information| D5
    VR -->|Saved resource record| AP

    AP -->|Teacher: automatically approve after successful validation and save| D3
    AP -->|Student: apply configured visibility policy| D3
    AP -->|Upload result and resource status| U

```

### Level 1 process explanation

1. 2.1 Validate Resource Input: Validate the title, resource type, file or URL, file format, and required metadata.
2. 2.2 Validate Folder and Subject: Confirm that the selected folder and subject exist and that the uploader has permission to use the folder.
3. 2.3 Check Storage Quota: Determine the user's role and verify that the upload fits within the remaining quota.
4. 2.4 Store File in Cloud: Store the file when the resource is file-based. A link-based resource does not need an uploaded file.
5. 2.5 Save Resource Metadata: Save the title, description, resource type, subject, folder, uploader, and current status.
6. 2.6 Record Resource Version: Record the initial version or a later version of the resource.
7. 2.7 Apply Approval and Visibility Rules: Automatically approve teacher uploads after successful validation and saving; apply the agreed policy for student uploads.

A real implementation should handle partial failures, including cloud uploads that succeed while metadata saving fails. It should also prevent concurrent uploads from exceeding the user's quota.

## 7.6 Additional Process — Folder Management

Folder management deserves its own detailed process because it is a core system feature.

```mermaid

flowchart TD
    A([Start]) --> B[User opens folder management]
    B --> C[Check authentication and permissions]
    C --> D{Authorized?}
    D -- No --> E[Display access denied]
    D -- Yes --> F{Select folder action}

    F -- Create --> G[Enter folder name and parent folder]
    G --> H[Validate name and parent permissions]
    H --> I{Valid?}
    I -- No --> G
    I -- Yes --> J[Save folder]

    F -- Rename --> K[Select folder and enter new name]
    K --> L[Validate permissions and name]
    L --> J

    F -- Move --> M[Select folder or resource and destination]
    M --> N[Check permissions and prevent folder cycles]
    N --> O{Move valid?}
    O -- No --> P[Display error]
    P --> F
    O -- Yes --> Q[Update parent or folder reference]

    F -- Remove --> R[Select folder to remove]
    R --> S[Check whether folder contains items]
    S --> T[Apply defined removal policy]
    T --> U[Update folder records and associations]

    J --> V[Display operation result]
    Q --> V
    U --> V
    V --> W([End])

```

Folder-management rules:

- Folders can contain subfolders and resources.
- Each folder has an owner or a defined access policy.
- Users may manage only folders for which they have permission.
- A folder cannot be moved inside itself or one of its descendants.
- Removing a non-empty folder requires a defined policy: reject the operation, move its contents, or remove its contents according to permissions.
- Moving a resource between folders should update its association without uploading the same file again.
- A folder name need not be globally unique; the chosen design may enforce uniqueness among siblings within the same parent folder.
