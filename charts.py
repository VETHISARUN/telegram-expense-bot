import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import tempfile, os

def pie_chart_from_dict(data: dict, title="Expenses by Category"):
    if not data:
        return None

    labels = list(data.keys())
    sizes = list(data.values())

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90, textprops={"fontsize": 8})
    ax.axis("equal")
    ax.set_title(title)

    path = _tempfile_path(".png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path

def _tempfile_path(suffix=".png"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        return tmp.name
