import tkinter as tk
from tkinter import font as tkfont
import math
import datetime

CANVAS_SIZE        = 520
CENTER             = CANVAS_SIZE // 2
CLOCK_RADIUS       = 220
FACE_BG            = "#F8F8F0"
FACE_RIM           = "#2C2C3E"
FACE_RIM_INNER     = "#3E3E55"
TICK_MAJOR_COLOR   = "#2C2C3E"
TICK_MINOR_COLOR   = "#9090A8"
NUMBER_COLOR       = "#1A1A2E"
HAND_HOUR_COLOR    = "#1A1A2E"
HAND_MINUTE_COLOR  = "#2C2C3E"
HAND_SECOND_COLOR  = "#E63946"
CENTER_DOT_COLOR   = "#E63946"
SHADOW_COLOR       = "#D0D0C8"
BG_COLOR           = "#EAEAF0"


CROWN_STEP_DEGREES = 6   


def polar_to_xy(angle_deg: float, radius: float, cx: float = CENTER, cy: float = CENTER):
    angle_rad = math.radians(angle_deg - 90)
    x = cx + radius * math.cos(angle_rad)
    y = cy + radius * math.sin(angle_rad)
    return x, y


def hand_polygon(angle_deg: float, length: float, width: float,
                 tail: float = 0.0, cx: float = CENTER, cy: float = CENTER):
    tip_x,  tip_y  = polar_to_xy(angle_deg,          length, cx, cy)
    tail_x, tail_y = polar_to_xy(angle_deg + 180,     tail,   cx, cy)
    left_x, left_y = polar_to_xy(angle_deg + 90,      width,  cx, cy)
    right_x,right_y= polar_to_xy(angle_deg - 90,      width,  cx, cy)
    return [left_x, left_y, tip_x, tip_y, right_x, right_y, tail_x, tail_y]


class ClockState:
    def __init__(self):
        self._offset_seconds: int = 0
        self.adjusting: bool = False

    def current_time(self) -> datetime.datetime:
        now = datetime.datetime.now()
        return now + datetime.timedelta(seconds=self._offset_seconds)

    def start_adjusting(self):
        self.adjusting = True

    def stop_adjusting(self):
        self.adjusting = False

    def adjust_minutes(self, delta: int):
        """Shift the displayed time by delta minutes."""
        self._offset_seconds += delta * 60

    def adjust_hours(self, delta: int):
        """Shift the displayed time by delta hours."""
        self._offset_seconds += delta * 3600

class AnalogClockApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Reloj Analógico")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_COLOR)

        self.state = ClockState()
        self._build_ui()
        self._draw_static_face()
        self._tick()

    def _build_ui(self):
        title_font = tkfont.Font(family="Helvetica", size=13, weight="bold")
        tk.Label(
            self.root, text="Reloj Analógico", font=title_font,
            bg=BG_COLOR, fg="#2C2C3E"
        ).pack(pady=(14, 2))

        self.canvas = tk.Canvas(
            self.root, width=CANVAS_SIZE, height=CANVAS_SIZE,
            bg=BG_COLOR, highlightthickness=0
        )
        self.canvas.pack(padx=20)

        readout_font = tkfont.Font(family="Courier", size=18, weight="bold")
        self.time_label = tk.Label(
            self.root, text="", font=readout_font,
            bg=BG_COLOR, fg="#2C2C3E"
        )
        self.time_label.pack(pady=(4, 2))

        self.status_label = tk.Label(
            self.root, text="", font=tkfont.Font(family="Helvetica", size=10),
            bg=BG_COLOR, fg="#888"
        )
        self.status_label.pack()

        self._build_crown_controls()


    def _build_crown_controls(self):
        frame = tk.Frame(self.root, bg=BG_COLOR)
        frame.pack(pady=8)

        btn_style = dict(
            bg="#2C2C3E", fg="white", relief="flat",
            font=tkfont.Font(family="Helvetica", size=11, weight="bold"),
            width=3, cursor="hand2", bd=0,
            activebackground="#E63946", activeforeground="white"
        )

        tk.Label(
            frame, text="Modificar Hora o minutos:", font=tkfont.Font(family="Helvetica", size=10),
            bg=BG_COLOR, fg="#555"
        ).pack(side="left", padx=(0, 8))

        tk.Label(frame, text="H:", bg=BG_COLOR, fg="#555",
                 font=tkfont.Font(family="Helvetica", size=10)).pack(side="left")

        self.btn_hour_back = tk.Button(
            frame, text="−", **btn_style,
            command=lambda: self._crown_adjust("hour", -1)
        )
        self.btn_hour_back.pack(side="left", padx=2)

        self.btn_hour_fwd = tk.Button(
            frame, text="+", **btn_style,
            command=lambda: self._crown_adjust("hour", +1)
        )
        self.btn_hour_fwd.pack(side="left", padx=(2, 12))

        tk.Label(frame, text="M:", bg=BG_COLOR, fg="#555",
                 font=tkfont.Font(family="Helvetica", size=10)).pack(side="left")

        self.btn_min_back = tk.Button(
            frame, text="−", **btn_style,
            command=lambda: self._crown_adjust("minute", -1)
        )
        self.btn_min_back.pack(side="left", padx=2)

        self.btn_min_fwd = tk.Button(
            frame, text="+", **btn_style,
            command=lambda: self._crown_adjust("minute", +1)
        )
        self.btn_min_fwd.pack(side="left", padx=2)
        tk.Button(
            frame, text="↺", bg="#888", fg="white", relief="flat", bd=0,
            font=tkfont.Font(family="Helvetica", size=11, weight="bold"),
            width=3, cursor="hand2",
            activebackground="#555", activeforeground="white",
            command=self._reset_time
        ).pack(side="left", padx=(12, 0))

    def _crown_adjust(self, unit: str, delta: int):
        """Called when a crown button is pressed."""
        self.state.start_adjusting()
        if unit == "hour":
            self.state.adjust_hours(delta)
        else:
            self.state.adjust_minutes(delta)
        self.root.after(600, self._resume_clock)
        self._update_display()

    def _resume_clock(self):
        self.state.stop_adjusting()

    def _reset_time(self):
        self.state._offset_seconds = 0
        self.state.stop_adjusting()
        self._update_display()

    def _draw_static_face(self):
        c = self.canvas
        cx, cy = CENTER, CENTER
        r = CLOCK_RADIUS

        c.create_oval(
            cx - r + 6, cy - r + 6, cx + r + 6, cy + r + 6,
            fill=SHADOW_COLOR, outline=""
        )

        c.create_oval(cx-r, cy-r, cx+r, cy+r,
                      fill=FACE_RIM, outline="", width=0)
        c.create_oval(cx-r+8, cy-r+8, cx+r-8, cy+r-8,
                      fill=FACE_RIM_INNER, outline="", width=0)

        face_r = r - 14
        c.create_oval(cx-face_r, cy-face_r, cx+face_r, cy+face_r,
                      fill=FACE_BG, outline="", width=0)

        for hour in range(12):
            angle = hour * 30
            outer_x, outer_y = polar_to_xy(angle, face_r - 4,  cx, cy)
            inner_x, inner_y = polar_to_xy(angle, face_r - 22, cx, cy)
            c.create_line(
                outer_x, outer_y, inner_x, inner_y,
                fill=TICK_MAJOR_COLOR, width=3, capstyle="round"
            )

        for minute in range(60):
            if minute % 5 == 0:
                continue
            angle = minute * 6
            outer_x, outer_y = polar_to_xy(angle, face_r - 4,  cx, cy)
            inner_x, inner_y = polar_to_xy(angle, face_r - 12, cx, cy)
            c.create_line(
                outer_x, outer_y, inner_x, inner_y,
                fill=TICK_MINOR_COLOR, width=1
            )

        num_font = tkfont.Font(family="Helvetica", size=16, weight="bold")
        for hour in range(1, 13):
            angle = hour * 30
            nx, ny = polar_to_xy(angle, face_r - 38, cx, cy)
            c.create_text(nx, ny, text=str(hour), font=num_font,
                          fill=NUMBER_COLOR)


    def _update_display(self):
        """Redraw the moving hands and update labels."""
        now = self.state.current_time()
        h, m, s = now.hour % 12, now.minute, now.second
        ms = now.microsecond / 1_000_000   

        second_angle = (s + ms)     * 6       
        minute_angle = (m + s/60)   * 6      
        hour_angle   = (h + m/60)   * 30         

        c    = self.canvas
        cx   = cy = CENTER
        fr   = CLOCK_RADIUS - 14   

        c.delete("hand")

        h_poly = hand_polygon(hour_angle, fr * 0.55, 7, tail=15, cx=cx, cy=cy)
        c.create_polygon(h_poly, fill=HAND_HOUR_COLOR, outline="",
                         smooth=False, tags="hand")

        m_poly = hand_polygon(minute_angle, fr * 0.82, 5, tail=20, cx=cx, cy=cy)
        c.create_polygon(m_poly, fill=HAND_MINUTE_COLOR, outline="",
                         smooth=False, tags="hand")

        s_tip_x,  s_tip_y  = polar_to_xy(second_angle,       fr * 0.90, cx, cy)
        s_tail_x, s_tail_y = polar_to_xy(second_angle + 180, fr * 0.18, cx, cy)
        c.create_line(s_tail_x, s_tail_y, s_tip_x, s_tip_y,
                      fill=HAND_SECOND_COLOR, width=2, capstyle="round",
                      tags="hand")

        jewel_r = 7
        c.create_oval(cx-jewel_r, cy-jewel_r, cx+jewel_r, cy+jewel_r,
                      fill=HAND_SECOND_COLOR, outline=FACE_RIM, width=2,
                      tags="hand")

        self.time_label.config(
            text=now.strftime("%I:%M:%S %p"),
            fg="#E63946" if self.state.adjusting else "#2C2C3E"
        )

        if self.state.adjusting:
            self.status_label.config(
                text="Ajustando manecillas — reloj en pausa", fg="#E63946"
            )
        else:
            offset = self.state._offset_seconds
            if offset == 0:
                self.status_label.config(text="Sincronizado con reloj del sistema", fg="#27AE60")
            else:
                sign = "+" if offset > 0 else ""
                h_off = offset // 3600
                m_off = (abs(offset) % 3600) // 60
                self.status_label.config(
                    text=f"Hora personalizada: {sign}{h_off}h {abs(m_off):02d}m",
                    fg="#E67E22"
                )

    def _tick(self):
        """Main loop — update display every ~50 ms for smooth movement."""
        if not self.state.adjusting:
            self._update_display()
        self.root.after(50, self._tick)

def main():
    root = tk.Tk()
    app = AnalogClockApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
