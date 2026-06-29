from __future__ import annotations


class MediaAssetError(Exception):
    code = "media_asset_error"
    http_status = 400

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class MediaAssetNotFound(MediaAssetError):
    code = "media_asset_not_found"
    http_status = 404
