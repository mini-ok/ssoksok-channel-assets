"""박자·시간표: 그림·효과·소리가 같은 표 하나를 읽는다. 모든 시각은 초, 순수 함수.

    B = Beat(bpm=120, beats_per_bar=4, fps=30)
    B.t(bar=3, beat=0)        # 3번째 마디 첫 박의 시각(마디·박은 0부터)
    B.snap(7.83)              # 가장 가까운 박으로
    B.hit(B.t(3))             # 소리 타격 정점 시각 = 화면 사건 + 1프레임
    Shots([('hook',4.5),('number',5.5)]).at(6.0) -> (index, name, local_t, dur)
"""
import bisect


class Beat:
    def __init__(self, bpm=120.0, beats_per_bar=4, fps=30, offset=0.0):
        self.bpm, self.bpb, self.fps, self.offset = float(bpm), beats_per_bar, fps, offset
        self.beat_len = 60.0 / self.bpm
        self.bar_len = self.beat_len * beats_per_bar

    def t(self, bar=0, beat=0.0):
        return self.offset + bar * self.bar_len + beat * self.beat_len

    def pos(self, t):
        """시각 → (마디, 박, 박 안 위상 0..1)."""
        b = max(0.0, (t - self.offset) / self.beat_len)
        return int(b // self.bpb), int(b % self.bpb), b % 1.0

    def snap(self, t, div=1):
        """가장 가까운 박(div=2면 반 박)."""
        q = self.beat_len / div
        return self.offset + round((t - self.offset) / q) * q

    def frame(self, t):
        return int(round(t * self.fps))

    def on_frame(self, t):
        """프레임 격자에 맞춘 시각."""
        return self.frame(t) / self.fps

    def hit(self, t_event, frames=1):
        """소리 정점은 화면 사건보다 한 프레임 뒤(먼저 들리면 어긋나 보인다)."""
        return self.on_frame(t_event) + frames / self.fps

    def pulse(self, t, sharp=6.0):
        """박마다 1에서 0으로 떨어지는 맥(빛·크기 맥동용)."""
        import math
        return math.exp(-sharp * self.pos(t)[2])

    def bars(self, t_end):
        n, out = 0, []
        while self.t(n) < t_end: out.append(self.t(n)); n += 1
        return out


class Shots:
    """[(이름, 길이초)] 샷 표. at(t)로 지금 샷과 샷 안 시각을 얻는다."""
    def __init__(self, items, start=0.0):
        self.items, self.starts, t = list(items), [], start
        for _, d in self.items: self.starts.append(t); t += d
        self.end = t

    def at(self, t):
        i = max(0, min(len(self.items) - 1, bisect.bisect_right(self.starts, t) - 1))
        name, d = self.items[i]
        return i, name, t - self.starts[i], d

    def cuts(self):
        return self.starts[1:]

    def fit_to(self, beat, div=1):
        """샷 길이를 박 격자에 맞춘 새 표(컷이 박에 떨어지게)."""
        out, t = [], self.starts[0] if self.starts else 0.0
        for name, d in self.items:
            e = beat.snap(t + d, div); e = e if e > t else t + beat.beat_len / div
            out.append((name, e - t)); t = e
        return Shots(out, self.starts[0] if self.starts else 0.0)
