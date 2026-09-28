# AWS S3 setup for company logos

This guide sets up a **private** S3 bucket for company logos and a dedicated IAM user that the API
uses to upload, read and delete them. No prior AWS experience is assumed.

## How logo storage works

- The bucket is **private**: "Block all public access" is on, so nobody can open a file by URL.
- The API validates each upload, stores it under `org-{organization_id}/logos/{random}.{ext}`, and
  saves only that **key** in the database.
- When a company is read, the API returns `logo_url`, a **presigned URL**. This is a normal S3 URL
  with a signature that is valid for 5 minutes (`AWS_QUERYSTRING_EXPIRE=300`). The browser loads it
  in an `<img>` tag, so the bucket needs no CORS configuration.
- The app's IAM user can only touch `org-*/logos/*` objects in this one bucket
  (least privilege).
- Without S3 (`USE_S3=False`, the default), logos are saved to `backend/media/` instead, so
  development never depends on AWS.

**Trade-offs:** signed URLs change on every request, so browser caching is weaker, and uploads pass
through the API server. At larger scale you would upload straight from the browser to S3 with a
presigned POST.

---

## Step 1: Create an AWS account

1. Go to <https://aws.amazon.com> and choose **Create an AWS Account**.
2. Enter an email address and an account name (e.g. `enclave-crm`), verify the email, and set a
   strong root password.
3. When asked to choose a plan, pick the **Free plan** if it is offered (at the time of writing,
   new accounts can choose a free plan that includes credits and cannot incur charges). Otherwise
   continue with the default plan; this project costs a few cents at most.
4. Enter a payment card (required for verification) and complete phone verification.
5. Choose the **Basic support (free)** plan and finish.
6. Sign in to the **AWS Management Console** as the **root user** with your email and password.

## Step 2: Secure the root user with MFA

The root user can do anything in the account, so protect it first.

1. In the console, click your account name (top right) and choose **Security credentials**.
2. Under **Multi-factor authentication (MFA)**, choose **Assign MFA device**.
3. Name it (e.g. `root-phone`), choose **Authenticator app**, and scan the QR code with Google
   Authenticator, Microsoft Authenticator, 1Password or similar.
4. Enter two consecutive codes from the app and choose **Add MFA**.

From now on, signing in as root asks for a code from your phone.

## Step 3: Create a budget alert (so you're never surprised by a bill)

1. In the top search bar type **Budgets** and open **Billing and Cost Management > Budgets**.
2. Choose **Create budget** and **Use a template (simplified)**.
3. Pick **Zero spend budget** (emails you as soon as any charge appears) or **Monthly cost budget**
   with an amount of **$5**.
4. Enter your email address and choose **Create budget**.

## Step 4: Choose a region

In the top-right corner of the console, open the region menu and choose one close to you, e.g.
**Asia Pacific (Mumbai) `ap-south-1`**. Note the code (e.g. `ap-south-1`): it becomes
`AWS_S3_REGION_NAME`.

## Step 5: Create the private bucket

1. Search for **S3** in the top bar and open it.
2. Choose **Create bucket**.
3. **Bucket type:** General purpose.
4. **Bucket name:** must be unique across all of AWS, lowercase, digits and hyphens only, e.g.
   `enclave-crm-logos-<your-initials>-<4 random digits>`. Note it: it becomes
   `AWS_STORAGE_BUCKET_NAME`.
5. **Object Ownership:** **ACLs disabled (recommended)**, which means the bucket owner owns every
   object.
6. **Block Public Access settings:** keep **Block all public access** **checked** (all four boxes).
7. **Bucket Versioning:** Disable.
8. **Default encryption:** **Server-side encryption with Amazon S3 managed keys (SSE-S3)**; Bucket
   Key can stay enabled.
9. Leave everything else as it is and choose **Create bucket**.

No bucket policy and no CORS configuration are needed.

## Step 6: Create a dedicated IAM user for the app

The app never uses your root credentials. It gets its own user that can only manage logo files.

1. Search for **IAM** and open it. Choose **Users** and then **Create user**.
2. **User name:** `crm-app-s3`. Leave **Provide user access to the AWS Management Console**
   **unchecked**, because this user is for code only. Choose **Next**.
3. **Permissions options:** choose **Attach policies directly**, select nothing, and choose **Next**,
   then **Create user**.
4. Open the new user `crm-app-s3`, go to the **Permissions** tab, and choose
   **Add permissions > Create inline policy**.
5. Switch the editor to **JSON**, delete what is there, and paste the policy below. Replace **both**
   occurrences of `YOUR_BUCKET_NAME` with your bucket name:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "LogoObjects",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/org-*/logos/*"
    },
    {
      "Sid": "ListBucketSoMissingFilesReturn404",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME"
    }
  ]
}
```

6. Choose **Next**, name the policy `crm-app-s3-logos`, and choose **Create policy**.

What the policy allows:

- **Objects:** upload, read and delete, but only keys matching `org-*/logos/*` in this bucket. The
  app cannot touch anything else, or any other bucket.
- **ListBucket:** before saving, django-storages checks whether the file name already exists. AWS
  only answers "not found" (404) to that check if the caller has `ListBucket`; otherwise it answers
  403 and the upload fails. The bucket holds only logos, so listing reveals nothing else.
  (`PROJECT_PLAN.md` §10 put a prefix condition on this statement; that condition only applies to
  list requests, not to this existence check, so it is removed. See `docs/DECISIONS.md`, D-008.)

## Step 7: Create an access key for the app

1. Still on the `crm-app-s3` user, open the **Security credentials** tab.
2. Under **Access keys**, choose **Create access key**.
3. **Use case:** choose **Local code** (or **Application running outside AWS**). AWS may suggest
   alternatives such as IAM roles; for local development an access key is fine. Tick the
   confirmation box and choose **Next**, then **Create access key**.
4. **Copy both values now.** The secret access key is shown **only once**. Use
   **Download .csv file** and keep it somewhere safe, outside the repository.

## Step 8: Configure the backend

1. Open `backend/.env` (never `backend/.env.example`) and set:

```dotenv
USE_S3=True
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=ap-south-1
AWS_ACCESS_KEY_ID=AKIA................
AWS_SECRET_ACCESS_KEY=........................................
AWS_QUERYSTRING_EXPIRE=300
```

2. Confirm git ignores the file. This command must print `backend/.env`:

```bash
git check-ignore backend/.env
```

3. Restart the backend (`make backend-dev`).

To go back to local files at any time, set `USE_S3=False`.

## Step 9: Verify

1. Log in to the app, create a company with a small logo (well under 2 MB), and open the company.
2. In the S3 console, open the bucket: the file appears under `org-<id>/logos/`.
3. The `logo_url` returned by the API opens the image. It contains `X-Amz-Signature=...`.
4. Copy the object's plain URL from the S3 console (**Object URL**) and open it in a private browser
   window: you get **AccessDenied**. The bucket is private.
5. Wait more than 5 minutes and reopen the old `logo_url`: you get **AccessDenied / Request has
   expired**.
6. Replace or remove the logo in the app: the old object disappears from the bucket.

## Security rules

- **Never commit keys.** `.env` files are git-ignored; only `.env.example` (with empty values) is
  committed. Check with `git log -p | grep -i AKIA`, which must print nothing.
- **Never paste keys into chats, issues or screenshots.**
- **If a key leaks:** in IAM, open `crm-app-s3`, go to **Security credentials**, **Deactivate** and
  then **Delete** the key, and create a new one. Removing it from git history is not enough.
- **In production on AWS** (EC2, ECS, EKS): don't use access keys at all. Attach an **IAM role**
  with the same policy to the instance or task, and leave `AWS_ACCESS_KEY_ID` and
  `AWS_SECRET_ACCESS_KEY` empty. boto3 picks up the role automatically.
- **Costs:** a handful of small logos is far inside any free allowance. The budget alert from step 3
  emails you if anything is ever charged.
