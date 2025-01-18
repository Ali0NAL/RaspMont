import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import socket
import json
import threading

app = dash.Dash(__name__)

data_store = {"cpu": [], "memory": [], "gpu": []}

def listen_data(server_ip="192.168.1.100", port=5000):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, port))
    buffer = b""
    while True:
        chunk = client_socket.recv(1024)
        if not chunk:
            print("Sunucu bağlantıyı kesti.")
            break
        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            line = line.strip()
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    data_store["cpu"].append(data["cpu_usage"])
                    data_store["memory"].append(data["memory_usage"])
                    data_store["gpu"].append(data["gpu_usage"])
                    data_store["cpu"] = data_store["cpu"][-100:]
                    data_store["memory"] = data_store["memory"][-100:]
                    data_store["gpu"] = data_store["gpu"][-100:]
                except json.JSONDecodeError:
                    print("Hatalı JSON verisi alındı.")

app.layout = html.Div([
    html.H1("Gerçek Zamanlı Sistem Verileri"),
    dcc.Graph(id="realtime-graph"),
    dcc.Interval(id="interval-component", interval=1000, n_intervals=0)
])

@app.callback(
    Output("realtime-graph", "figure"),
    [Input("interval-component", "n_intervals")]
)
def update_graph(n):
    return {
        "data": [
            {"x": list(range(len(data_store["cpu"]))), "y": data_store["cpu"], "type": "line", "name": "CPU (%)"},
            {"x": list(range(len(data_store["memory"]))), "y": data_store["memory"], "type": "line", "name": "Bellek (%)"},
            {"x": list(range(len(data_store["gpu"]))), "y": data_store["gpu"], "type": "line", "name": "GPU (%)"},
        ],
        "layout": {
            "title": "Gerçek Zamanlı Sistem Verileri",
            "xaxis": {"title": "Zaman"},
            "yaxis": {"title": "Yüzde (%)"}
        }
    }

if __name__ == "__main__":
    threading.Thread(target=listen_data, daemon=True).start()
    app.run_server(debug=True, host="0.0.0.0")
