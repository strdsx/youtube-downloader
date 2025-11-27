import streamlit as st
from yt_dlp import YoutubeDL
import sys
import io

class StdoutCapture:
    """stdout을 캡처하기 위한 래퍼 클래스"""
    def __init__(self, buffer):
        self._buffer = buffer
        # buffer 속성을 자기 자신으로 설정 (yt-dlp가 sys.stdout.buffer를 사용)
        self.buffer = self
    
    def write(self, data):
        if isinstance(data, bytes):
            self._buffer.write(data)
        else:
            self._buffer.write(data.encode('utf-8'))
        return len(data)
    
    def flush(self):
        pass
    
    def close(self):
        # close 호출을 무시 (버퍼를 닫지 않음)
        pass

def download_video(url):
    """YouTube 영상을 다운로드하고 버퍼와 파일명을 반환합니다."""
    
    # 먼저 비디오 정보 추출 (다운로드 없이)
    with YoutubeDL({
        "quiet": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["default", "-tv_simply"],
            },
        },
    }) as ydl:
        info = ydl.extract_info(url, download=False)
        video_id = info.get('id', 'video')
        title = info.get('title', 'video')
        # 파일명에 사용할 수 없는 문자 제거
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{video_id}_{safe_title}.mp4"
    
    # 실제 다운로드 (버퍼로)
    buffer = io.BytesIO()
    
    # stdout을 버퍼로 임시 교체
    original_stdout = sys.stdout
    sys.stdout = StdoutCapture(buffer)
    
    try:
        ydl_opts = {
            "outtmpl": "-",  # stdout으로 출력
            "format": "best[ext=mp4]/best",  # mp4 형식 우선
            "logtostderr": True,  # 로그는 stderr로
            "extractor_args": {
                "youtube": {
                    "player_client": ["default", "-tv_simply"],
                },
            },
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # 버퍼의 내용을 가져오기 (버퍼를 닫기 전에)
        video_data = buffer.getvalue()
        
    finally:
        # stdout 복원
        sys.stdout = original_stdout
    
    return video_data, filename

# Streamlit 앱
st.set_page_config(page_title="YouTube 다운로더", page_icon="🎥", layout="centered")

st.title("🎥 YouTube 영상 다운로더")
st.write("YouTube 영상 링크를 입력하면 MP4 파일로 다운로드할 수 있습니다.")

# URL 입력
url = st.text_input("**YouTube URL:**", placeholder="https://www.youtube.com/watch?v=...")

if st.button("다운로드", type="primary"):
    if url:
        try:
            with st.spinner("영상을 추출하는 중입니다..."):
                # 버퍼를 활용한 다운로드
                video_bytes, filename = download_video(url)
                
                if video_bytes:
                    st.success("✅ 다운로드가 완료되었습니다!")
                    
                    # 다운로드 버튼 제공
                    st.download_button(
                        label="📥 파일 다운로드",
                        data=video_bytes,
                        file_name=filename,
                        mime="video/mp4"
                    )
                else:
                    st.error("다운로드한 파일이 비어있습니다.")
                    
        except Exception as e:
            st.error(f"❌ 오류가 발생했습니다: {str(e)}")
    else:
        st.warning("⚠️ YouTube URL을 입력해주세요.")

st.divider()
