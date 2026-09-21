# Beginner AWS Console Guide

This guide starts from opening the AWS Console. It uses the two existing buckets supplied for this project. AWS console labels can change slightly.

## Part 1 — Understand the Result

You will configure this flow:

```text
Upload JPEG/PNG to source S3 → S3 invokes Lambda → Pillow resizes it → Lambda saves it in destination S3
```

Reference settings:

| Setting | Value |
|---|---|
| Region | Europe (Stockholm), `eu-north-1` |
| Source bucket | `YOUR-SOURCE-BUCKET` |
| Destination bucket | `YOUR-DESTINATION-BUCKET` |
| Function | `s3-image-resizer` |
| Runtime | Python 3.12 |
| Architecture | x86_64 |
| Maximum output | 800 × 800 pixels |

Use your own globally unique bucket names if these buckets are not in your account.

## Part 2 — Sign In and Select the Region

1. Open [AWS Management Console](https://console.aws.amazon.com/).
2. Sign in with an IAM or IAM Identity Center user. Avoid daily work with the root user.
3. At the upper-right corner, open the Region menu.
4. Select **Europe (Stockholm) — eu-north-1**.
5. Keep Lambda and both buckets in this Region. S3 bucket names are global, but every bucket has one home Region.

## Part 3 — Check the Two S3 Buckets

1. In the top search bar, type **S3**.
2. Open **S3**.
3. Choose **General purpose buckets**.
4. Confirm that your source and destination project buckets exist.
5. Open the source bucket and choose **Properties**. Confirm its AWS Region is `eu-north-1`.
6. Repeat for the destination bucket.
7. In each bucket, open **Permissions**.
8. Confirm **Block all public access** is **On**. The buckets do not need to be public.

If a bucket is missing, choose **Create bucket**, select `eu-north-1`, enter a new globally unique lowercase name, keep Block Public Access enabled, and choose **Create bucket**. Replace the old name everywhere in the policy and Lambda configuration.

## Part 4 — Create a Least-Privilege IAM Policy

1. In the top search bar, type **IAM** and open it.
2. In the left menu, choose **Policies**.
3. Choose **Create policy**.
4. Choose the **JSON** editor.
5. Delete the sample JSON.
6. Copy the complete contents of `iam/lambda-s3-policy.json` from this repository and paste it.
7. Replace `YOUR-SOURCE-BUCKET` with your actual source bucket name.
8. Replace `YOUR-DESTINATION-BUCKET` with your actual destination bucket name.
9. Do not put an account ID, password or access key in this policy.
10. Choose **Next**.
11. For Policy name, enter `lambda-image-resizer-s3-policy`.
12. Add this description: `Read source images and write resized images to the destination bucket.`
13. Choose **Create policy**.

This policy does not allow deleting objects, listing every bucket, or reading the destination bucket.

## Part 5 — Create the Lambda Execution Role

1. In IAM, choose **Roles**.
2. Choose **Create role**.
3. For Trusted entity type, select **AWS service**.
4. For Use case, select **Lambda**.
5. Choose **Next**.
6. Search for and select `AWSLambdaBasicExecutionRole`. This managed policy permits CloudWatch logging.
7. Search for and select `lambda-image-resizer-s3-policy`.
8. Choose **Next**.
9. For Role name, enter `lambda-image-resizer-role`.
10. Review the two policies and choose **Create role**.

## Part 6 — Create the Pillow Lambda Layer

Pillow is an external binary dependency. The layer and Lambda function must use the same Python version and processor architecture. This project uses **Python 3.12** and **x86_64** because the tested Pillow layer contains CPython 3.12 x86_64 Linux binaries.

If you already have a compatible `pillow-layer.zip`:

1. In the AWS search bar, type **Lambda** and open it.
2. In the left menu, choose **Layers**.
3. Choose **Create layer**.
4. For Name, enter `pillow-python312-x86-64`.
5. Select **Upload a .zip file**.
6. Choose **Upload** and select your private `pillow-layer.zip`.
7. For Compatible architectures, select **x86_64**.
8. For Compatible runtimes, select **Python 3.12**.
9. Choose **Create**.

The ZIP should contain a top-level `python/` directory with `PIL/` and the installed Pillow package inside it. Keep your local layer ZIP private; this repository does not distribute it.

To rebuild a compatible layer yourself on Linux, AWS CloudShell or WSL:

```bash
chmod +x scripts/build-layer.sh
./scripts/build-layer.sh
```

The script creates `pillow-layer-python312-x86_64.zip`. Do not build the native Pillow package on ordinary Windows and expect it to work in Lambda's Linux environment.

## Part 7 — Create the Lambda Function

1. In the AWS search bar, type **Lambda** and open it.
2. Choose **Functions** in the left menu.
3. Choose **Create function**.
4. Select **Author from scratch**.
5. For Function name, enter `s3-image-resizer`.
6. For Runtime, select **Python 3.12**.
7. For Architecture, select **x86_64**.
8. Expand **Change default execution role**.
9. Select **Use an existing role**.
10. Select `lambda-image-resizer-role`.
11. Choose **Create function**.

## Part 8 — Attach the Layer and Add the Code

1. On the function page, scroll to **Layers**.
2. Choose **Add a layer**.
3. Select **Custom layers**.
4. Select `pillow-python312-x86-64` and its latest version.
5. Choose **Add**.
6. Open the **Code** tab.
7. Open `lambda_function.py` in the inline editor.
8. Replace the sample code with the complete contents of `src/lambda_function.py` from this repository.
9. Choose **Deploy**.
10. Open **Runtime settings** and choose **Edit**.
11. Confirm Handler is `lambda_function.lambda_handler`.
12. Choose **Save** if you made a change.

Do not also upload the all-in-one dependency ZIP when using the Pillow layer. Use one dependency method to keep the setup clear.

## Part 9 — Add Environment Variables

1. Open the function's **Configuration** tab.
2. Choose **Environment variables**.
3. Choose **Edit**.
4. Add these keys and values:

| Key | Value |
|---|---|
| `DESTINATION_BUCKET` | `YOUR-DESTINATION-BUCKET` |
| `OUTPUT_PREFIX` | `resized` |
| `MAX_WIDTH` | `800` |
| `MAX_HEIGHT` | `800` |
| `JPEG_QUALITY` | `85` |
| `MAX_INPUT_BYTES` | `10485760` |

5. Choose **Save**.

## Part 10 — Configure Memory, Timeout and Log Retention

1. Under **Configuration**, choose **General configuration**.
2. Choose **Edit**.
3. Set Memory to **512 MB**.
4. Set Timeout to **30 seconds**.
5. Choose **Save**.
6. In a new console tab, search for **CloudWatch** and open it.
7. Choose **Logs** → **Log groups**.
8. After the first invocation, select `/aws/lambda/s3-image-resizer`.
9. Choose **Actions** → **Edit retention setting**.
10. Select **14 days** and save. This prevents indefinite log retention for the lab.

## Part 11 — Add the S3 Trigger

1. Return to the Lambda function page.
2. In **Function overview**, choose **Add trigger**.
3. Select **S3**.
4. For Bucket, select your source bucket (`YOUR-SOURCE-BUCKET`).
5. For Event types, select **All object create events**.
6. Leave Prefix empty.
7. For Suffix, you may leave it empty because the code safely skips unsupported files. One notification cannot accept several suffixes at once.
8. Read and select the recursive invocation acknowledgement.
9. Choose **Add**.

The output bucket is different from the trigger bucket, so resized files do not invoke the function again. Lambda adds the required resource-based permission when the trigger is created through the console.

## Part 12 — Test with a Real Image

1. Open **S3**.
2. Open the source bucket.
3. Choose **Upload**.
4. Choose **Add files** and select a `.jpg`, `.jpeg`, or `.png` image smaller than 10 MiB.
5. Choose **Upload**.
6. Wait approximately 10–30 seconds.
7. Open the destination bucket.
8. Open the `resized/` folder.
9. Confirm the uploaded filename exists.
10. Download the output and check that its width and height are no greater than 800 pixels.

Expected example:

```text
Source:      holiday/photo.jpg
Destination: resized/holiday/photo.jpg
```

## Part 13 — Check Lambda and CloudWatch

1. Open Lambda → **Functions** → `s3-image-resizer`.
2. Open the **Monitor** tab.
3. Confirm at least one invocation and no error.
4. Choose **View CloudWatch logs**.
5. Open the newest log stream.
6. Look for a line beginning with `Resized s3://`.
7. Confirm it contains the expected source and destination keys.

## Part 14 — Test Important Cases

### Test A: JPEG

Upload a large `.jpg`. Confirm that a JPEG appears in `resized/` and stays within 800 × 800.

### Test B: PNG

Upload a `.png`. Confirm that the output remains PNG.

### Test C: Folder key and spaces

Create or upload to a source prefix such as `class photos/my image.jpg`. Confirm the destination key is `resized/class photos/my image.jpg`. This verifies URL decoding and folder preservation.

### Test D: Unsupported file

Upload a `.txt` file. Confirm that no output is written and the log says the object was skipped.

### Test E: Oversized input

Upload an image larger than 10 MiB only if you understand the cost. The function should fail with `Input object exceeds MAX_INPUT_BYTES`. Delete the object afterward.

## Part 15 — Troubleshooting

| Problem | Check |
|---|---|
| `No module named PIL` | Confirm the Pillow layer is attached and both layer and function use Python 3.12 x86_64 |
| `AccessDenied` on GetObject | Source ARN and `s3:GetObject` permission in the custom policy |
| `AccessDenied` on PutObject | Destination ARN and `s3:PutObject` permission; KMS permissions if applicable |
| No invocation | Same Region, source bucket trigger, ObjectCreated event and Lambda resource policy |
| No output but invocation succeeded | File extension must be JPG, JPEG or PNG; check warning logs |
| Trigger validation error | Remove stale S3 event notifications whose destination no longer exists |
| Task timed out | Increase timeout/memory or lower maximum input size |
| Layer works on one runtime only | Native files such as `cpython-312-x86_64-linux-gnu.so` require Python 3.12 and x86_64 |

## Part 16 — Security and Cost Checks

1. Keep both S3 buckets private.
2. Never put AWS access keys in the Python file, README, ZIP, screenshots or GitHub.
3. Use only the bucket-scoped IAM policy included here.
4. If using customer-managed KMS keys, grant the execution role only the required decrypt/encrypt permissions.
5. Check AWS Billing and Cost Management after the lab. S3 storage/requests, Lambda execution and CloudWatch Logs can incur charges.
6. Do not assume a budget alert blocks spending; it is a notification.

## Part 17 — Cleanup

Perform cleanup only when you no longer need the lab:

1. Open Lambda → `s3-image-resizer` → **Configuration** → **Triggers**.
2. Select the S3 trigger and choose **Delete**.
3. Delete the Lambda function.
4. Open S3 and empty only the two lab buckets after downloading anything needed.
5. Delete the lab buckets if they are no longer required.
6. Open IAM and delete `lambda-image-resizer-role` and `lambda-image-resizer-s3-policy` if nothing else uses them.
7. Open Lambda → **Layers** and delete the unused Pillow layer version if no function uses it.
8. Open CloudWatch Logs and delete `/aws/lambda/s3-image-resizer` if it still exists.
9. Recheck the Region and Billing console for leftover resources.

## Evidence Checklist

Store no private information in screenshots. Useful evidence includes:

- Source bucket object list
- Lambda trigger and environment-variable names (not secrets)
- Successful Lambda invocation metrics
- Destination `resized/` object list
- Original and resized dimensions
- CloudWatch success log

Do not claim AWS testing as complete until these checks have been performed in the actual account.
