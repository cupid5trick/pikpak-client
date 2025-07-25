from fileinput import filename
from hashlib import md5, sha1
from io import BufferedReader, BytesIO
import json
import os
from pathlib import Path
from typing import Any, Optional

import oss2

from pikpakapi import PikPakApi, PikpakException


def gcid_hash_file(obj: Any) -> Optional[str]:
    """
    Use GCID algorithm to compute file hash. References:
    - 迅雷Hash算法分析 | Binuxの杂货铺: https://binux.blog/2012/03/hash_algorithm_of_xunlei/
    - Problems with pikpak storing hash after uploads · Issue #7838: https://github.com/rclone/rclone/issues/7838#issuecomment-2106396466
    """
    h = sha1()
    size = os.path.getsize(obj)
    psize = 0x40000
    while size / psize > 0x200 and psize < 0x200000:
        psize = psize << 1

    with open(obj, "rb") as stream:
        data = stream.read(psize)
        while data:
            h.update(sha1(data).digest())
            data = stream.read(psize)
    return h.hexdigest().upper()


class PikPakClient(PikPakApi):
    async def file_upload(
        self, file_path: str, parent_path: str, file_name: Optional[str] = None
    ):
        """
        Upload a file to PikPak using the official API and Aliyun OSS.
        Args:
            file_path: Path to the file to upload
            parent_path: PikPak folder to upload into
            file_name: Optional, override the file name
        Returns:
            PikPak file/task info dict
        """
        self.file_list
        folder_id = await self.path_to_id(parent_path)
        folder_id = folder_id[-1].get("id") if folder_id else None
        return await self._file_upload(file_path, folder_id, file_name)

    async def _file_upload(
        self, file_path: str, parent_id: str, file_name: Optional[str] = None
    ):
        """
        Upload a file to PikPak using the official API and Aliyun OSS.
        Args:
            file_path: Path to the file to upload
            parent_id: PikPak folder ID to upload into
            file_name: Optional, override the file name
        Returns:
            PikPak file/task info dict
        """
        if not os.path.isfile(file_path):
            raise PikpakException(f"File not found: {file_path}")
        file_name = file_name or os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        # Step 1: Initiate upload with PikPak API

        meta = {
            "hash": gcid_hash_file(Path(file_path)),
            "name": file_name,
            "size": str(file_size),
            "kind": "drive#file",
            "id": "",
            "parent_id": parent_id,
            "upload_type": "UPLOAD_TYPE_RESUMABLE",
            "folder_type": "NORMAL",
            "resumable": {"provider": "PROVIDER_ALIYUN"},
        }
        # Optionally add hash, etc.
        url = f"https://{self.PIKPAK_API_HOST}/drive/v1/files"
        headers = self.get_headers()
        resp_json = await self._request_post(url, meta, headers)

        # Step 2: Extract OSS credentials and upload info
        try:
            if resp_json["task"]["phase"] == "PHASE_TYPE_COMPLETE":
                return resp_json
            oss_info = resp_json["resumable"]["params"]
            bucket = oss_info["bucket"]
            endpoint = f"https://{oss_info['endpoint'] if not bucket in oss_info['endpoint'] else oss_info['endpoint'].strip(bucket+'\.')}"
            access_key_id = oss_info["access_key_id"]
            access_key_secret = oss_info["access_key_secret"]
            security_token = oss_info["security_token"]
            key = oss_info["key"]
        except Exception as e:
            raise PikpakException(f"Failed to parse OSS credentials: {e}\n{resp_json}")
        # Step 3: Upload file to OSS using oss2
        auth = oss2.StsAuth(access_key_id, access_key_secret, security_token)
        bucket_obj = oss2.Bucket(auth, endpoint, bucket)
        # Use multipart upload for large files
        try:
            total_size = file_size
            part_size = 5 * 1024 * 1024  # 5MB
            upload_id = bucket_obj.init_multipart_upload(key).upload_id
            parts = []
            with open(file_path, "rb") as f:
                part_number = 1
                while True:
                    data = f.read(part_size)
                    if not data:
                        break
                    result = bucket_obj.upload_part(key, upload_id, part_number, data)
                    parts.append(oss2.models.PartInfo(part_number, result.etag))
                    part_number += 1
            bucket_obj.complete_multipart_upload(key, upload_id, parts)
        except Exception as e:
            raise PikpakException(f"OSS upload failed: {e}")
        # Step 4: Return PikPak file/task info
        return resp_json
