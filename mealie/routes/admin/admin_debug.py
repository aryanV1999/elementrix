import os
import shutil
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends

from mealie.core.dependencies.dependencies import get_temporary_path
from mealie.routes._base import BaseAdminController, controller
from mealie.schema.admin.debug import DebugResponse
from mealie.schema.openai.general import OpenAIText
from mealie.services.openai import OpenAILocalImage, OpenAIService
from mealie.schema.user.user import User
from mealie.core.dependencies.auth import get_current_user


router = APIRouter(prefix="/debug")

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@controller(router)
class AdminDebugController(BaseAdminController):

    @router.post("/openai", response_model=DebugResponse)
    async def debug_openai(
        self,
        image: UploadFile | None = File(None),
        current_user: User = Depends(get_current_user)
    ):

        # SECURITY FIX: restrict endpoint to administrators
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        if not self.settings.OPENAI_ENABLED:
            return DebugResponse(success=False, response="OpenAI is not enabled")

        if image and not self.settings.OPENAI_ENABLE_IMAGE_SERVICES:
            return DebugResponse(
                success=False,
                response="Image was provided, but OpenAI image services are not enabled"
            )

        with get_temporary_path() as temp_path:

            if image:

                # SECURITY FIX: validate file size
                file_data = await image.read()

                if len(file_data) > MAX_FILE_SIZE:
                    raise HTTPException(status_code=400, detail="Uploaded file too large")

                # SECURITY FIX: sanitize filename to prevent path traversal
                safe_filename = Path(image.filename).name

                file_path = temp_path.joinpath(safe_filename)

                with file_path.open("wb") as buffer:
                    buffer.write(file_data)

                local_images = [
                    OpenAILocalImage(
                        filename=os.path.basename(file_path),
                        path=file_path
                    )
                ]

            else:
                local_images = None

            try:
                openai_service = OpenAIService()
                prompt = openai_service.get_prompt("debug")

                message = "Hello, checking to see if I can reach you."

                if local_images:
                    message = f"{message} Here is an image to test with:"

                response = await openai_service.get_response(
                    prompt,
                    message,
                    response_schema=OpenAIText,
                    images=local_images
                )

                if not response:
                    raise Exception("No response received from OpenAI")

                return DebugResponse(
                    success=True,
                    response=f'OpenAI is working. Response: "{response.text}"'
                )

            except Exception as e:

                # SECURITY FIX: log internal error but do not expose details to client
                self.logger.exception(e)

                return DebugResponse(
                    success=False,
                    response="OpenAI request failed. Error logged on server."
                )