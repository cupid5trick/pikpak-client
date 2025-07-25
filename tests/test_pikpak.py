import asyncio
from base64 import b64decode
from fileinput import filename
import hashlib
from io import BufferedReader
import json
import logging
import os
import random
import string
import tempfile
from typing import Any
import unittest

from dotenv import load_dotenv

from pikpakapi import PikPakApi
from pikpakapi.pikpak import PikPakClient, gcid_hash_file


log_handlers = [logging.StreamHandler()]
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=log_handlers,
)
logger = logging.getLogger(__name__)


async def login(client: PikPakApi):
    await client.login()
    await client.refresh_access_token()
    # await client.refresh


async def test_features(client: PikPakApi):
    """结论：没有实现文件上传。
    可以继承 PikPakAPI 类自行实现。
    ck0.ABuKkcchOlrbB4MMUy5g2UVYW41IyFD4CdW_apXvN824gneloZfi9XE8I2Nmkg_nAPnKP5VMtxUpaXYYkGJK6KhCT37hwkhMEVnJTCZ_DDngNwKP5XT3kOzzLxPwNbsT-fIGHNGH6FLhTDSO2HRES8nzA8xc1WUwvwVoJ8tcnjL1hFPGIUZhZ_t3h2b3SjV43VVpJMSOH9gFdtOCQLu7y8lU6ebspPa0C7FtOAsL_OeRI1sQHymDiI5pFUhvF1O1i90uZ6Va81pO6rIA3_7duGr2qDpxnZhLJBAFyCrQ-pTl2MK9RS5gdyK44SHzu0ItgsvK2GZh2YkaIEZQwVeqnA.ClAI7ozBxIMzEhBZVU14NW5JOFpVOEFwOHBtGgUyLjAuMCIMbXlwaWtwYWsuY29tKiBlMGZhYmMwNWE1NWQ0ZWM2OTEyYmQ5ZWQ3OTBkYWIxMBKAAasAfY1ykqsaqfE5HVVSaS5s11xVbfnP4X6GzW5P5UuPvvN1SftQTyBjTVZKjcqwEdhBZpWOBlmiTPXdU_DdTEsjyoxsjCvvl0p1VARGsYUEhh2BP9QQMdtyR50pllyQwEIr8hRaHT81KN0PCxy1H1wlY9KqqUY8jJNslOno1Ct2
    ck0.ZK9884XfgpXqtqKA21q0yslGxzidSCmPG_rEQaLMV8evXdCDUcM-lb-mgqPahPSZMQ3oqfJhRe3uzcXvZDNxYzlwzPvIvgMjYUEpWmdSlx6kJ_Clx9qDQq-ogQAfJPEjv5hTn0tjZ0xE6tMOsa2PpzfwOk1oxatFnKUNa2k8Nrd_7oBCyMN3muyLo55K8d-xwdRjGGssDlZZLibgoEEyCXAYko-yqw3Unh7-jp0Mp6i9sKYRVCpd0N4YHcuoov4j
    'ck0.kH_jZYwEZwqi_VmRofP_xl8XwVUayKVs4O1IQIDXsx-4qcJJzDQCZjRhMtqXBrGiTQHQqMiLwtAEXyHz7_dBzMhWK_VWEru8j76wvQZ59O4aXepAd3tNI9E-f674OL4e51GtJ8h48EJxKeQt8wawBLQMwfy0VYjEz81hCK6CukjdnWLLLLBTFoNL8dis2snVFQTntoxS5-5p-2I7Fr1nk-4p8CXwoQrHHmNYRtjoq0L369ThJ1abegNVnYn3uoPY'

    """

    def f(x: Any) -> str:
        return json.dumps(x, indent=2, ensure_ascii=False)

    fpath = "/My Pack/tmp/test/"
    res = await client.offline_list()
    logger.debug(f"offline_list: {f(res)}")
    u_quota = await client.get_quota_info()
    logger.debug(f"quota: {f(u_quota)}")
    t_quota = await client.get_transfer_quota()
    logger.debug(f"transfer quota: {f(t_quota)}")
    u_info = client.get_user_info()
    logger.debug(f"user info: {f(u_info)}")
    vip_info = await client.vip_info()
    logger.debug(f"vip info: {f(vip_info)}")
    ids = await client.path_to_id(fpath)
    logger.debug(f"path id: {f(ids)}")
    fileid = ids[-1]["id"]
    f_info = await client.file_list(parent_id=fileid)
    logger.debug(f"f_info for {fpath}: {f(f_info)}")
    ids = await client.path_to_id(f"{fpath}/test.txt")
    fileid = ids[-1]["id"]
    url_info = await client.get_download_url(fileid)
    logger.debug(f"file info for download: {f(url_info)}")
    logger.debug(
        f"download url: {url_info["medias"][0]["link"]["url"] if url_info['medias'] else url_info['web_content_link']}"
    )


class PikPakApiTest(unittest.TestCase):
    def setUp(self) -> None:
        # 邮箱登录会触发captcha实人验证，需要手机号登录
        self.assertTrue(load_dotenv(dotenv_path="tests/.env"), "Failed to load dotenv!")
        user = os.getenv("PIKPAK_USERNAME")
        passwd = os.getenv("PIKPAK_PASSWORD")
        logger.debug(f"Login in with {user}:{passwd}")
        self.client = PikPakClient(
            # username="vp001.cupid5trick@gmail.com",
            username=user,
            password=passwd,
        )

        asyncio.run(login(self.client))
        return super().setUp()

    # @unittest.skip("verified")
    def test_pikpak_func(self):
        """测试 pikpakapi 基本功能"""
        asyncio.run(test_features(self.client))

    # @unittest.skip("verified")
    def test_pikpak_upload(self):
        def create_tmp_file_with_random_text(size_bytes):
            # Generate random text of specified size
            chars = string.ascii_letters + string.digits + string.punctuation + " \n"
            random_text = "".join(random.choices(chars, k=size_bytes))

            # Create a temporary file
            tmp = tempfile.NamedTemporaryFile(
                mode="w+", delete=False
            )  # delete=False keeps the file after closing
            tmp.write(random_text)
            tmp.flush()  # Ensure all content is written to disk
            print(f"Temporary file created at: {tmp.name}")
            return tmp.name

        async def upload():
            folder = "/My Pack/tmp/test"
            filename = "tests/test.txt"  #
            # filename = create_tmp_file_with_random_text(4*1024)

            await self.client.file_upload(filename, folder)

        asyncio.run(upload())


class DigestTest(unittest.TestCase):

    def test_osfilesize(self):
        file_path = "tests/test.txt"
        with open(file_path, "rb") as f:
            data = f.read()
        self.assertTrue(
            len(data) == os.path.getsize(file_path),
            "Bytes read-in not equal to the value of os.path.size()",
        )

    # @unittest.skip("excluded")
    def test_hash_method(self):
        # The hash value from the log
        expected_hash = "B3BADB40ED4B3843AD4BC89E8244524EE02564B3"
        # The file to test (replace with the actual file path used in the log)
        file_path = "tests/test.txt"
        # Read file bytes
        with open(file_path, "rb") as f:
            data = f.read()
        # Try various hash methods
        hashes = {
            "md5": hashlib.md5(data).hexdigest().upper(),
            "sha1": hashlib.sha1(data).hexdigest().upper(),
            "sha224": hashlib.sha224(data).hexdigest().upper(),
            "sha256": hashlib.sha256(data).hexdigest().upper(),
            "sha384": hashlib.sha384(data).hexdigest().upper(),
            "sha512": hashlib.sha512(data).hexdigest().upper(),
            "sha3_224": hashlib.sha3_224(data).hexdigest().upper(),
            "sha3_256": hashlib.sha3_256(data).hexdigest().upper(),
            "sha3_384": hashlib.sha3_384(data).hexdigest().upper(),
            "sha3_512": hashlib.sha3_512(data).hexdigest().upper(),
            "blake2b": hashlib.blake2b(data).hexdigest().upper(),
            "blake2s": hashlib.blake2s(data).hexdigest().upper(),
            # SHAKE128/256 are variable length, so you can try 20 bytes (40 hex chars)
            "shake_128_20": hashlib.shake_128(data).hexdigest(20).upper(),
            "shake_256_20": hashlib.shake_256(data).hexdigest(20).upper(),
            "xunlei_gcid": gcid_hash_file(file_path),
        }
        for name, digest in hashes.items():
            print(f"{name}:\t\t{digest}")
        # Assert at least one matches
        self.assertIn(
            expected_hash, hashes.values(), f"No hash matches {expected_hash}"
        )


if __name__ == "__main__":
    unittest.main()
