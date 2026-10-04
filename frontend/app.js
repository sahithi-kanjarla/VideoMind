const loadForm = document.querySelector('#load-form');
const askForm = document.querySelector('#ask-form');
const errorBox = document.querySelector('#error');
const loadStatus = document.querySelector('#load-status');
let activeVideoId = null;
let player = null;
let youtubeApiReady = null;

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function clearError() {
  errorBox.hidden = true;
  errorBox.textContent = '';
}

function ensureYoutubeApi() {
  if (window.YT?.Player) return Promise.resolve();
  if (youtubeApiReady) return youtubeApiReady;
  youtubeApiReady = new Promise((resolve, reject) => {
    const previous = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => { previous?.(); resolve(); };
    const script = document.createElement('script');
    script.src = 'https://www.youtube.com/iframe_api';
    script.onerror = () => reject(new Error('The YouTube player could not be loaded.'));
    document.head.append(script);
  });
  return youtubeApiReady;
}

async function makePlayer(videoId) {
  await ensureYoutubeApi();
  if (player) { player.loadVideoById(videoId); return; }
  document.querySelector('#player').replaceChildren();
  player = new YT.Player('player', {
    videoId,
    width: '100%',
    height: '100%',
    playerVars: {playsinline: 1, origin: location.origin},
  });
}

loadForm.addEventListener('submit', async (event) => {
  event.preventDefault(); clearError();
  const button = document.querySelector('#load-button');
  button.disabled = true; loadStatus.textContent = 'Fetching transcript and preparing the video…';
  document.querySelector('#video-section').hidden = true;
  document.querySelector('#question').disabled = true;
  document.querySelector('#ask-button').disabled = true;
  try {
    const response = await fetch('/api/youtube/load', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:document.querySelector('#youtube-url').value.trim()})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Could not load this video.');
    activeVideoId = data.video_id;
    document.querySelector('#video-title').textContent = data.title;
    document.querySelector('#video-section').hidden = false;
    await makePlayer(data.video_id);
    document.querySelector('#question').disabled = false;
    document.querySelector('#ask-button').disabled = false;
    document.querySelector('#answer-section').hidden = true;
    loadStatus.textContent = `Ready · ${data.chunks} transcript chunks indexed`;
  } catch (error) { showError(error.message); loadStatus.textContent = 'Video could not be loaded.'; }
  finally { button.disabled = false; }
});

askForm.addEventListener('submit', async (event) => {
  event.preventDefault(); clearError();
  const question = document.querySelector('#question');
  const button = document.querySelector('#ask-button');
  button.disabled = true; button.textContent = 'Thinking…';
  try {
    const response = await fetch('/api/chat/query', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({video_id:activeVideoId,question:question.value.trim()})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Could not answer this question.');
    document.querySelector('#answer-text').textContent = data.answer;
    const sources = document.querySelector('#sources');
    sources.replaceChildren(...data.sources.map((source) => {
      const link = document.createElement('button');
      link.type = 'button'; link.textContent = `[${source.label}]`;
      link.addEventListener('click', () => player?.seekTo(source.start, true));
      return link;
    }));
    document.querySelector('#answer-section').hidden = false;
  } catch (error) { showError(error.message); }
  finally { button.disabled = false; button.textContent = 'Ask'; }
});
