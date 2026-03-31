import tkinter as tk


def _is_descendant(widget, ancestor):
    while widget is not None:
        if widget == ancestor:
            return True
        widget = getattr(widget, "master", None)
    return False


def bind_mousewheel_to_canvas(scope_widget: tk.Widget, canvas: tk.Canvas) -> None:
    """Scroll a canvas when wheel events come from widgets inside the given scope."""

    def _on_mousewheel(event):
        if not _is_descendant(event.widget, scope_widget):
            return None

        if getattr(event, "num", None) == 4:
            canvas.yview_scroll(-1, "units")
            return "break"

        if getattr(event, "num", None) == 5:
            canvas.yview_scroll(1, "units")
            return "break"

        delta = getattr(event, "delta", 0)
        if delta == 0:
            return None

        units = max(1, int(abs(delta) / 120))
        direction = -1 if delta > 0 else 1
        canvas.yview_scroll(direction * units, "units")
        return "break"

    scope_widget.bind_all("<MouseWheel>", _on_mousewheel, add="+")
    scope_widget.bind_all("<Button-4>", _on_mousewheel, add="+")
    scope_widget.bind_all("<Button-5>", _on_mousewheel, add="+")


def attach_scrollable_frame(canvas: tk.Canvas, scrollable_frame: tk.Widget) -> int:
    """Embed a frame in a canvas and keep it sized to the visible canvas width."""
    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    scrollable_frame.bind(
        "<Configure>",
        lambda event: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.bind(
        "<Configure>",
        lambda event: canvas.itemconfigure(window_id, width=event.width),
        add="+"
    )
    return window_id
