# Integration Walkthrough

The Bank of Singapore Portal UI has been successfully integrated with the FinDoc Extraction API backend.

## Changes Made

### 1. Backend Schema Update
Modified [backend/schemas.py](file:///Users/jayaprakash/Claude/api/backend/schemas.py) to recognize all document categories presented in the frontend (e.g., `income_tax`, `payslips`, `biz_reg`, etc.).
- Mapped specific document types where appropriate (e.g. `income_tax` mapping to [NOAData](file:///Users/jayaprakash/Claude/api/backend/schemas.py#16-18), `payslips` to [PaySlipData](file:///Users/jayaprakash/Claude/api/backend/schemas.py#25-27)).
- Created a new [OtherDocData](file:///Users/jayaprakash/Claude/api/backend/schemas.py#33-35) model to act as a fallback for the remaining document types, ensuring they are accepted and saved by the backend without throwing validation errors.

### 2. Frontend Submission Integration
Updated the [handleSubmit](file:///Users/jayaprakash/Claude/api/bos-portal/app.js#456-513) JavaScript function in [bos-portal/app.js](file:///Users/jayaprakash/Claude/api/bos-portal/app.js) to dynamically POST documents to the API instead of simulating a slow delay.
- It iterates over all uploaded documents for the selected profile and calls `POST http://localhost:8000/sessions/extract` passing the `doc_types` and [file](file:///Users/jayaprakash/Claude/api/backend/Dockerfile) as `FormData`.
- It intelligently propagates the `session_id` returned from the first upload request to seamlessly link the rest of the uploaded documents into the same session.
- It utilizes the real returned `session_id` from the backend to generate the `BOS-...` submission reference number rather than just generating a random number locally.
- Added error handling with UI toast notifications if any of the API requests fail.

## How to Test
1. Start the backend by running `docker compose up backend` in your `api/` directory.
2. Open [bos-portal/index.html](file:///Users/jayaprakash/Claude/api/bos-portal/index.html) in your browser.
3. Log in with the default credentials (`demo` / `gdo2024`).
4. Select a profile and upload any PDF/JPG testing files.
5. Click **Submit Documents**. The UI will now upload the documents directly to the backend database!
