# Copyright (c) 2019, The Linux Foundation. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#    * Neither the name of The Linux Foundation nor the names of its
#      contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import time
import logging


from .iotccsdk.camera import CameraClient
log = logging.getLogger(__name__)


def take_picture(ip_addr, username="admin", password="admin"):
    with CameraClient.connect(ip_address=ip_addr, username=username, password=password) as camera_client:
        #print('supported resolutions: ' + str(camera_client.resolutions))
        #print('supported encodetype: ' + str(camera_client.encodetype))
        #print('supported bitrates: ' + str(camera_client.bitrates))
        #print('supported framerates: ' + str(camera_client.framerates))
        #print(camera_client.configure_preview(resolution="1080P", display_out=1))
        camera_client.configure_preview(resolution="1080P", display_out=1)
        camera_client.set_preview_state("on")
        log.info("Preview started")

        log.info("Taking snapshot")
        if not camera_client.captureimage():
            return "captureimage failed"
        log.info("Snapshot taken")
        camera_client.set_preview_state("off")
        log.info("Preview stopped")

        camera_client.logout()
        log.info("Logged out")

        return "captureimage successful"



