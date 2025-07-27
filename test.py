import asyncio
import json
import logging
import os
import sys

import httpx
from dotenv import load_dotenv
from pikpakapi import PikPakApi

logger = logging.getLogger("test")


def f(obj):
    return json.dumps(obj, indent=4, ensure_ascii=False)


async def log_token(client, extra_data):
    logging.info(f"Token: {client.encoded_token}, Extra Data: {extra_data}")


async def test():
    user = os.getenv("PIKPAK_USERNAME")
    passwd = os.getenv("PIKPAK_PASSWORD")
    client = PikPakApi(
        username=user,
        password=passwd,
        httpx_client_args={
            # "proxy": "http://127.0.0.1:7890",
            "transport": httpx.AsyncHTTPTransport(retries=3),
        },
        token_refresh_callback=log_token,
        token_refresh_callback_kwargs={"extra_data": "test"},
    )
    await client.login()
    await client.refresh_access_token()
    tasks = await client.offline_list()
    logger.debug(f(tasks))
    logger.debug("=" * 30)
    if tasks.get("tasks"):
        await client.delete_tasks(task_ids=[tasks["tasks"][0]["id"]])
    logger.debug(f(client.get_user_info()))
    logger.debug("=" * 30)

    logger.debug(
        f(await client.offline_download(
            "magnet:?xt=urn:btih:42b46b971332e776e8b290ed34632d5c81a1c47c")))
    logger.debug("=" * 30)
    offline_info = await client.offline_list()
    logger.debug(f(offline_info))
    logger.debug("=" * 30)
    logger.debug(f(offline_info))
    logger.debug("=" * 30)
    fileid = offline_info["tasks"][0]["file_id"]
    logger.debug(
        f(await client.file_list(
            parent_id=(await client.path_to_id("/My Pack"))[-1]["id"])))
    logger.debug(f(await client.get_download_url(fileid)))
    logger.debug(f(await client.offline_file_info(fileid)))

    logger.debug(
        f(await client.file_rename(
            "VNayNjZtsdmka4YrwZWVj-r4o1",
            "[Nekomoe kissaten][Deaimon][11][1080p][CHS]_01.mp4",
        )))
    logger.debug("=" * 30)

    logger.debug(
        f(await client.file_batch_star(ids=["VN6qSS-FBcaI6l7YltWsjUU1o1"])))
    logger.debug("=" * 30)

    logger.debug(
        f(await client.file_batch_unstar(ids=["VN6qSS-FBcaI6l7YltWsjUU1o1"])))
    logger.debug("=" * 30)

    logger.debug(f(await client.file_star_list()))
    logger.debug("=" * 30)

    logger.debug(
        f(await client.file_batch_share(ids=["VN6qSS-FBcaI6l7YltWsjUU1o1"],
                                        need_password=True)))
    logger.debug("=" * 30)

    logger.debug(f(await client.get_quota_info()))
    logger.debug("=" * 30)

    logger.debug(
        f(await client.get_share_info(
            "https://mypikpak.com/s/VO8BcRb-0fibD0Ncymp8nxSMo1")))

    test_restore = await client.get_share_info(
        "https://mypikpak.com/s/VO8BcRb-0fibD0Ncymp8nxSMo1/VO8Ba45l-FRcCf559uZjwjFjo1"
    )

    await client.restore(
        share_id="VO8BcRb-0fibD0Ncymp8nxSMo1",
        pass_code_token=test_restore.get("pass_code_token"),
        file_ids=[
            "VO8BcNTLpxHtBHDFH0d5cGRzo1",
        ],
    )


async def test_save():
    client = PikPakApi(
        username="your_username",
        password="your_password",
    )
    await client.login()
    await client.refresh_access_token()
    with open("pikpak.json", "w") as f:
        f.write(f(client.to_dict()))

    with open("pikpak.json", "r") as f:
        data = json.load(f)
        client = PikPakApi.from_dict(data)
        await client.refresh_access_token()
        logger.debug(f(client.get_user_info()))
        logger.debug(
            f(
                await client.get_share_info(
                    "https://mypikpak.com/s/VO8BcRb-0fibD0Ncymp8nxSMo1"
                )
            )
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    if not load_dotenv("tests/.env"):
        logging.error("Failed to load dotenv (.env)")
        sys.exit(-1)
    asyncio.run(test())
    asyncio.run(test_save())
