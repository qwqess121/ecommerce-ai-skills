"""
FFmpeg 视频关键帧提取器
- 比 PyAV 快 5-10x
- 自动按时长选择采样间隔
- 默认生成拼合缩略图（composite.jpg），也可输出单帧
- composite 模式：只需读1张图，token消耗降低 ~80%

依赖: ffmpeg 已在 PATH 中（或传入 ffmpeg_path 参数）
用法:
    python extract_frames.py <video_path> [output_dir] [--single] [--width W] [--max N]
"""

import subprocess, sys, os, json, re, argparse
from pathlib import Path


def get_duration(video_path: str, ffprobe: str = 'ffprobe', ffmpeg: str = 'ffmpeg') -> float:
    """用ffprobe获取视频时长（秒），失败则用ffmpeg -i回退解析"""
    cmd = [
        ffprobe, '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        val = float(r.stdout.strip())
        if val > 0:
            return val
    except Exception:
        pass
    # 用 ffmpeg -i 解析 Duration 行作为回退
    try:
        r2 = subprocess.run([ffmpeg, '-i', video_path], capture_output=True, text=True)
        for line in (r2.stdout + r2.stderr).splitlines():
            if 'Duration:' in line:
                # Duration: 00:00:13.45,
                m = re.search(r'Duration:\s*(\d+):(\d+):([\d.]+)', line)
                if m:
                    h, mn, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
                    return h * 3600 + mn * 60 + s
    except Exception:
        pass
    return 30.0  # 最终回退


def pick_interval(duration: float, max_frames: int) -> tuple[float, int]:
    """根据时长选采样间隔，返回 (interval_sec, n_frames)"""
    if duration <= 30:
        interval = 2.0
    elif duration <= 60:
        interval = 5.0
    else:
        interval = 10.0
    n = int(duration / interval)
    # 不超过 max_frames
    if n > max_frames:
        interval = duration / max_frames
        n = max_frames
    return interval, max(n, 1)


def extract_composite(
    video_path: str,
    output_dir: str,
    width: int = 320,
    max_frames: int = 10,
    quality: int = 5,
    ffmpeg: str = 'ffmpeg',
) -> str:
    """
    提取帧并拼合为一张横向缩略图矩阵。
    返回 composite.jpg 的路径。
    token 消耗：1张图 vs 逐帧多张。
    """
    os.makedirs(output_dir, exist_ok=True)
    duration = get_duration(video_path, ffmpeg=ffmpeg)
    interval, n_frames = pick_interval(duration, max_frames)

    fps_str = f'1/{interval:.1f}'    # e.g. "1/2.0"
    # scale: width固定，高度自动（保持比例）；tile: n_frames x 1
    vf = f'fps={fps_str},scale={width}:-2,tile={n_frames}x1'

    out_path = str(Path(output_dir) / 'composite.jpg')
    cmd = [
        ffmpeg, '-y', '-i', video_path,
        '-vf', vf,
        '-frames:v', '1',
        '-q:v', str(quality),
        out_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'FFmpeg error:\n{r.stderr}')

    size_kb = os.path.getsize(out_path) // 1024
    print(f'[frames] composite → {out_path}  ({n_frames} frames, {size_kb} KB)')

    # 保存元数据
    meta = {
        'video': video_path,
        'duration_sec': duration,
        'n_frames': n_frames,
        'interval_sec': interval,
        'frame_width_px': width,
        'composite': out_path,
        'timestamps': [round(interval * i, 1) for i in range(n_frames)],
    }
    meta_path = str(Path(output_dir) / 'frames_meta.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)

    return out_path


def extract_single(
    video_path: str,
    output_dir: str,
    width: int = 480,
    max_frames: int = 10,
    quality: int = 5,
    ffmpeg: str = 'ffmpeg',
) -> list[str]:
    """
    提取单独帧文件（frame_00.jpg ... frame_N.jpg），压缩宽度。
    返回文件路径列表。
    """
    os.makedirs(output_dir, exist_ok=True)
    duration = get_duration(video_path, ffmpeg=ffmpeg)
    interval, n_frames = pick_interval(duration, max_frames)

    fps_str = f'1/{interval:.1f}'
    vf = f'fps={fps_str},scale={width}:-2'
    pattern = str(Path(output_dir) / 'frame_%02d.jpg')

    cmd = [
        ffmpeg, '-y', '-i', video_path,
        '-vf', vf,
        '-q:v', str(quality),
        pattern,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'FFmpeg error:\n{r.stderr}')

    paths = sorted(Path(output_dir).glob('frame_*.jpg'))
    total_kb = sum(p.stat().st_size for p in paths) // 1024
    print(f'[frames] {len(paths)} frames → {output_dir}/ ({total_kb} KB total)')

    meta = {
        'video': video_path,
        'duration_sec': duration,
        'n_frames': len(paths),
        'interval_sec': interval,
        'frame_width_px': width,
        'files': [str(p) for p in paths],
        'timestamps': [round(interval * i, 1) for i in range(len(paths))],
    }
    meta_path = str(Path(output_dir) / 'frames_meta.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)

    return [str(p) for p in paths]


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='FFmpeg frame extractor')
    ap.add_argument('video', help='Input video path')
    ap.add_argument('output_dir', nargs='?', default=None, help='Output directory (default: <video_dir>/frames)')
    ap.add_argument('--single', action='store_true', help='Output individual frames instead of composite')
    ap.add_argument('--width', type=int, default=320, help='Frame width in pixels (default: 320)')
    ap.add_argument('--max', type=int, default=10, help='Max frames (default: 10)')
    ap.add_argument('--quality', type=int, default=5, help='JPEG quality 2-31, lower=better (default: 5)')
    ap.add_argument('--ffmpeg', default='ffmpeg', help='Path to ffmpeg binary')
    args = ap.parse_args()

    video = args.video
    out_dir = args.output_dir or str(Path(video).parent / 'frames')

    if args.single:
        paths = extract_single(video, out_dir, args.width, args.max, args.quality, args.ffmpeg)
        print('Files:', paths)
    else:
        path = extract_composite(video, out_dir, args.width, args.max, args.quality, args.ffmpeg)
        print('Composite:', path)
