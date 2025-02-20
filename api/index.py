from http.server import BaseHTTPRequestHandler
import subprocess
import os
from urllib.parse import urlparse, parse_qs
import json

# 如果 是 mac 则使用 remote-cpu-cli-mac
if os.uname().sysname == 'Darwin':
    client = "remote-cpu-cli-mac"
else:
    client = "remote-cpu-cli"




# 尝试创建 ./tmp
# os.makedirs("./tmp", exist_ok=True)

tmp_dir = "./tmp"
cli_path = f"{tmp_dir}/{client}"

# 打印当前目录
print(os.getcwd())

# 如果./tmp/remote-cpu-cli 不存在 则下载
if not os.path.exists(cli_path):
    # 下载 remote-cpu-cli
    subprocess.run(["wget", "https://drive.google.com/uc?export=download&id=1zaAGNihs1rY2KTwKAV3BJfuiXQ4bFGus", "-O", cli_path])

if os.path.exists(cli_path):
    os.chmod(cli_path, 0o755)
# 如果 ./tmp/remote-cpu-cli 不存在 则下载
log_file = f"{tmp_dir}/logs/output_{os.getpid()}.log"

os.makedirs(os.path.dirname(log_file), exist_ok=True)
if not os.path.exists(log_file):
    try:
        with open(log_file, 'w') as f:
            f.write('')
        print(f"Log file created successfully at: {log_file}")
    except Exception as e:
        print(f"Error creating log file: {e}")

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
         # 读取 POST 请求的内容
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        request_data = json.loads(post_data.decode('utf-8'))
        
        line = request_data.get('commands', '')

        # print("line===", line)
        
        # 构建命令行参数
        args = []
        for param in line.split():
            if param.startswith('--') or param.startswith('-'):
                # 如果 没有 =,        
                if '=' not in param:
                    args.append(param)
                else:
                    key, value = param.split('=')
                    args.extend([key, value])
        
        if not os.path.exists(cli_path):
            response_data = {
                'status': 'error',
                'error': f'CLI executable not found at {cli_path}'
            }
        else:
            try:
                # 使用追加模式而不是覆盖模式
                command = f"{cli_path} {' '.join(args)} >> {log_file} 2>&1"
                process = subprocess.Popen(
                    command,
                    shell=True,
                    text=True
                )
                # 不等待完成，直接返回成功状态
                response_data = {
                    'status': 'success',
                    'command': command,
                    'log_file': log_file
                }
            except Exception as e:
                # print("e===", e)
                response_data = {
                    'status': 'error',
                    'error': str(e)
                }
        
        self.send_response(200)
        # 在 commands 路由中
        self.send_header('Content-type', 'application/json; charset=utf-8')
        
        # 在默认路由中
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

        return

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)


        query_params_path = query_params.get('path', [''])[0]

        if query_params_path == 'logs':
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = f.read()
            else:
                logs = ''

            # print(logs)
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(logs.encode('utf-8'))
            return

        # 原有的默认路由处理
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        self.wfile.write('Hello, world!'.encode('utf-8'))
        return


    # get /command?line=123

