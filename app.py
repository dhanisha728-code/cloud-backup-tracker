
import os
import uuid
import hashlib
import boto3
import mysql.connector
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, send_file
)
from io import BytesIO
from dotenv import load_dotenv

from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "development-key")

BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "cloud_backup_tracker"),
        connection_timeout=5
    )


@app.route("/")
def index():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM backups ORDER BY backup_time DESC"
        )
        backups = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    return render_template("index.html", backups=backups)


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")

    if not file or not file.filename:
        flash("Please select a file.")
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)

    if not filename:
        flash("Invalid filename.")
        return redirect(url_for("index"))

    connection = None
    cursor = None
    object_key = f"backups/{uuid.uuid4().hex}_{filename}"

    try:
        file.stream.seek(0, 2)
        file_size = file.stream.tell()
        file.stream.seek(0)

# Calculate SHA-256 checksum of the uploaded file
        sha256_hash = hashlib.sha256()

        for chunk in iter(lambda: file.stream.read(1024 * 1024), b""):
            sha256_hash.update(chunk)

        checksum = sha256_hash.hexdigest()

# Reset file position before uploading to S3
        file.stream.seek(0)

# Upload the actual file to AWS S3
        s3.upload_fileobj(file.stream, BUCKET_NAME, object_key)

        # Save the file details in MySQL
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO backups
            (file_name, stored_name, file_size, backup_status, checksum_sha256)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (filename, object_key, file_size, "Success", checksum)
        )
        connection.commit()
        flash("Success! File uploaded to AWS S3 and saved in MySQL.")
        connection.commit()
        flash("Success! File uploaded to AWS S3 and saved in MySQL.")

    except Exception as error:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Upload failed")
        flash(f"Upload failed: {error}")

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("index"))


@app.route("/download/<int:backup_id>")
def download(backup_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM backups WHERE id = %s",
            (backup_id,)
        )
        backup = cursor.fetchone()
    finally:
        cursor.close()
        connection.close()

    if not backup or backup["backup_status"] != "Success":
        flash("Backup not found or not available.")
        return redirect(url_for("index"))

    try:
        response = s3.get_object(
            Bucket=BUCKET_NAME,
            Key=backup["stored_name"]
        )

        return send_file(
            BytesIO(response["Body"].read()),
            as_attachment=True,
            download_name=backup["file_name"]
        )

    except Exception:
        app.logger.exception("Download failed")
        flash("Download failed. Check the terminal for details.")
        return redirect(url_for("index"))





@app.route("/verify/<int:backup_id>")
def verify_integrity(backup_id):
    connection = None
    cursor = None

    try:
        # Get backup details from MySQL
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM backups WHERE id = %s",
            (backup_id,)
        )
        backup = cursor.fetchone()

        if not backup:
            flash("Backup not found.")
            return redirect(url_for("index"))

        saved_checksum = backup.get("checksum_sha256")

        if not saved_checksum:
            flash("No checksum found. Upload this file again to enable verification.")
            return redirect(url_for("index"))

        # Download the stored file from S3 into memory
        response = s3.get_object(
            Bucket=BUCKET_NAME,
            Key=backup["stored_name"]
        )

        file_data = response["Body"].read()

        # Calculate the checksum of the stored file
        actual_checksum = hashlib.sha256(file_data).hexdigest()

        # Compare the saved checksum with the current checksum
        if actual_checksum == saved_checksum:
            flash("Integrity verified! The backup file is unchanged.")
        else:
            flash("INTEGRITY WARNING! The stored file does not match its saved checksum.")

    except Exception:
        app.logger.exception("Integrity verification failed")
        flash("Verification failed. Check the VS Code terminal for details.")

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("index"))
@app.route("/delete/<int:backup_id>", methods=["POST"])
def delete_backup(backup_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM backups WHERE id = %s",
            (backup_id,)
        )
        backup = cursor.fetchone()

        if not backup:
            flash("Backup not found.")
            return redirect(url_for("index"))

        # Delete the file from AWS S3
        s3.delete_object(
            Bucket=BUCKET_NAME,
            Key=backup["stored_name"]
        )

        # Delete the record from MySQL
        cursor.execute(
            "DELETE FROM backups WHERE id = %s",
            (backup_id,)
        )

        connection.commit()

        if cursor.rowcount >= 0:
            flash("Backup deletion completed. Check the dashboard.")
        else:
            flash("No matching database record was deleted.")

    except Exception:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Delete backup failed")
        flash("Delete failed. Check the VS Code terminal.")

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
