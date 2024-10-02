from typing import Tuple
from api.api import Api
from api.post import Post  # needed to call transform function

"""
FloorplanToBlender3d
Copyright (C) 2021 Daniel Westberg
"""


def create_file(ref, id, iformat, file):
    """Write incoming data to file"""
    # Extract the actual image data from the form data
    boundary = b'------WebKitFormBoundary'
    parts = file.split(boundary)
    for part in parts:
        if b'Content-Disposition: form-data; name="data"; filename=' in part:
            # Find the start of the actual image data
            image_data_start = part.find(b'\r\n\r\n') + 4
            image_data = part[image_data_start:]
            break
    else:
        raise ValueError("Image data not found in the form data")

    file_path = ref.shared.parentPath + "/" + ref.shared.imagesPath + "/" + id + iformat
    with open(file_path, "wb") as f:
        f.write(image_data)

class Put(Api):
    def __init__(self, client, shared_variables):
        super().__init__(client, shared_variables)
        # All all viable functions here!
        self.dispatched_calls["create"] = self.create
        self.dispatched_calls["createandtransform"] = self.createandtransform

    def create(
        self, id: str, hash: str, iformat: str, file: bytes, *args, **kwargs
    ) -> Tuple[str, bool]:
        """
        Upload new image to server.
        @Return List[ response, status]
        """
        # id and hash correct exist?
        status = True
        if (id, hash, False) in self.shared.all_ids:

            # format supported?
            if (
                iformat in self.shared.supported_image_formats
                or iformat in self.shared.supported_config_formats
                or iformat in self.shared.supported_stacking_formats
            ):

                create_file(self, id, iformat, file)

                # update saved file status
                index = self.shared.all_ids.index((id, hash, False))
                self.shared.all_ids[index] = (id, hash, True)
                message = "File uploaded!"

                # trigger index update for gui!
                self.shared.reindex_files()
            else:
                message = "Image format not supported!"
                status = False
        elif (id, hash, True) in self.shared.all_ids:
            message = "File with same name already exist!"
            status = False
        else:
            message = "Wrong ID or HASH!"
            status = False
        return message, status

    def createandtransform(
        self,
        id: str,
        hash: str,
        iformat: str,
        oformat: str,
        file: bytes,
        *args,
        **kwargs
    ) -> Tuple[str, bool]:
        """
        Send image to server and start transform process
        @Return List[ response, status]
        """
        (message, status) = self.create(id=id, hash=hash, iformat=iformat, file=file)
        message += " "
        if status:
            message += Post(client=self.client, shared_variables=self.shared).transform(
                func="transform", id=id, oformat=oformat
            )
        return message, status
