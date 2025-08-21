let cameraStreams = {};

async function toggleLaptopCamera(id) {
    const videoElement = document.getElementById(`cameraVideo${id}`);
    const button = document.getElementById(`toggleBtn${id}`);

    if (cameraStreams[id]) {
        cameraStreams[id].getTracks().forEach(track => track.stop());
        cameraStreams[id] = null;
        videoElement.srcObject = null;
        button.textContent = "Bật Camera";
    } else {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            videoElement.srcObject = stream;
            cameraStreams[id] = stream;
            button.textContent = "Tắt Camera";
        } catch (err) {
            alert("Không thể truy cập camera: " + err);
        }
    }
}

function openFullscreen(id) {
    const videoElement = document.getElementById(`cameraVideo${id}`);
    const overlay = document.getElementById("videoOverlay");
    const fullscreenVideo = document.getElementById("fullscreenVideo");

    if (videoElement.srcObject) {
        fullscreenVideo.srcObject = videoElement.srcObject;
    }

    // Thêm class để phóng to
    fullscreenVideo.classList.add("big-size");

    overlay.style.display = "flex";
}

function closeFullscreen() {
    const overlay = document.getElementById("videoOverlay");
    overlay.style.display = "none";

    const fullscreenVideo = document.getElementById("fullscreenVideo");
    fullscreenVideo.srcObject = null;

    // Bỏ class khi đóng
    fullscreenVideo.classList.remove("big-size");
}


