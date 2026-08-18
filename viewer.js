async function init(siteKey) {
  const cfg = await fetch('/api/config').then(r => r.json());
  const site = cfg[siteKey] || { layout: '1x1', cameras: [0] };
  const root = document.getElementById('grid');
  root.className = 'grid ' + site.layout;

  for (const idx of site.cameras) {
    const cam = cfg.cameras[idx];
    if (!cam) continue;

    const tile = document.createElement('div');
    tile.className = 'tile';

    const video = document.createElement('video');
    video.autoplay = true;
    video.muted = true;
    video.playsInline = true;

    const label = document.createElement('div');
    label.className = 'label';
    label.textContent = cam.name;

    const pipBtn = document.createElement('button');
    pipBtn.className = 'pip-btn';
    pipBtn.textContent = 'PiP';
    pipBtn.onclick = async () => {
      try {
        if (document.pictureInPictureElement) {
          await document.exitPictureInPicture();
        } else if (video.readyState >= 2) {
          await video.requestPictureInPicture();
        }
      } catch (err) {
        console.error('PiP error:', err);
      }
    };

    tile.appendChild(video);
    tile.appendChild(label);
    tile.appendChild(pipBtn);
    root.appendChild(tile);

    const stream = `/hls/cam${idx}/stream.m3u8`;

    if (Hls.isSupported()) {
      const hls = new Hls({
        liveSyncDurationCount: 1,
        liveMaxLatencyDurationCount: 3,
        enableWorker: true
      });
      hls.loadSource(stream);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => video.play().catch(()=>{}));
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = stream;
      video.addEventListener('loadedmetadata', () => video.play().catch(()=>{}));
    }
  }
}
