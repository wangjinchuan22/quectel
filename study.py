"""学习进度分解系统。

用法示例：
	python study.py create --title "Python 入门" --goal "能写出小项目" \
		--content "变量与类型\n条件与循环\n函数\n文件与异常"
	python study.py show
	python study.py update 1 --done
	python study.py update 2 --progress 60
"""

from __future__ import annotations

import argparse
import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DATA_FILE = Path(__file__).with_name("learning_plans.json")


@dataclass
class LearningTask:
	id: int
	title: str
	description: str
	estimated_minutes: int
	progress: int = 0
	done: bool = False


@dataclass
class LearningStage:
	id: int
	title: str
	objective: str
	tasks: list[LearningTask] = field(default_factory=list)


@dataclass
class LearningPlan:
	title: str
	goal: str
	created_at: str
	stages: list[LearningStage] = field(default_factory=list)

	@property
	def progress(self) -> int:
		tasks = [task for stage in self.stages for task in stage.tasks]
		if not tasks:
			return 0
		return round(sum(task.progress for task in tasks) / len(tasks))


def split_content(content: str) -> list[str]:
	"""将换行、编号列表或句号分隔的内容转换为学习主题。"""
	items = re.split(r"[\n；;。]+", content)
	result = []
	for item in items:
		cleaned = re.sub(r"^\s*(?:[-*•]|\d+[.)、])\s*", "", item).strip()
		if cleaned and cleaned not in result:
			result.append(cleaned)
	return result


def build_plan(title: str, goal: str, content: str) -> LearningPlan:
	topics = split_content(content)
	if not topics:
		raise ValueError("学习内容不能为空，请用换行或分号分隔知识点。")

	stage_titles = ["基础认知", "核心练习", "综合应用"]
	stages: list[LearningStage] = []
	chunk_size = max(1, (len(topics) + 2) // 3)

	for stage_index, start in enumerate(range(0, len(topics), chunk_size), start=1):
		stage_topics = topics[start : start + chunk_size]
		tasks = [
			LearningTask(
				id=start + task_index + 1,
				title=f"掌握：{topic}",
				description=f"理解“{topic}”的核心概念，并完成一个最小练习。",
				estimated_minutes=max(25, min(90, len(topic) * 5 + 20)),
			)
			for task_index, topic in enumerate(stage_topics)
		]
		stages.append(
			LearningStage(
				id=stage_index,
				title=stage_titles[min(stage_index - 1, len(stage_titles) - 1)],
				objective=f"完成 {', '.join(stage_topics)}，为下一阶段建立基础。",
				tasks=tasks,
			)
		)

	return LearningPlan(
		title=title,
		goal=goal,
		created_at=datetime.now().isoformat(timespec="seconds"),
		stages=stages,
	)


def save_plan(plan: LearningPlan) -> None:
	DATA_FILE.write_text(
		json.dumps(asdict(plan), ensure_ascii=False, indent=2), encoding="utf-8"
	)


def plan_payload(plan: LearningPlan) -> dict[str, Any]:
	payload = asdict(plan)
	payload["progress"] = plan.progress
	return payload


def load_plan() -> LearningPlan:
	if not DATA_FILE.exists():
		raise FileNotFoundError("还没有学习计划，请先使用 create 创建计划。")
	data: dict[str, Any] = json.loads(DATA_FILE.read_text(encoding="utf-8"))
	stages = [
		LearningStage(
			id=stage["id"],
			title=stage["title"],
			objective=stage["objective"],
			tasks=[LearningTask(**task) for task in stage["tasks"]],
		)
		for stage in data["stages"]
	]
	return LearningPlan(
		title=data["title"],
		goal=data["goal"],
		created_at=data["created_at"],
		stages=stages,
	)


def print_plan(plan: LearningPlan) -> None:
	print(f"\n学习计划：{plan.title}")
	print(f"目标：{plan.goal}")
	print(f"总进度：{plan.progress}%\n")
	for stage in plan.stages:
		print(f"阶段 {stage.id}：{stage.title} - {stage.objective}")
		for task in stage.tasks:
			status = "已完成" if task.done else f"{task.progress}%"
			print(f"  [{task.id}] {task.title} ({task.estimated_minutes} 分钟) - {status}")


def update_task(task_id: int, progress: int | None, done: bool) -> None:
	plan = load_plan()
	for stage in plan.stages:
		for task in stage.tasks:
			if task.id == task_id:
				task.done = done or progress == 100
				task.progress = 100 if task.done else (progress if progress is not None else task.progress)
				save_plan(plan)
				print(f"已更新任务 [{task.id}]，当前进度 {task.progress}%。")
				return
	raise ValueError(f"找不到任务编号：{task_id}")


WEB_PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>学习进度工作台</title>
  <style>
    :root { --ink: #17324d; --muted: #6d7d8d; --paper: #f4f7f5; --line: #dce6e2; --teal: #0f766e; --coral: #e76f51; }
    * { box-sizing: border-box; }
    body { margin: 0; color: var(--ink); font: 15px/1.6 "Microsoft YaHei", "Noto Sans SC", sans-serif; background: radial-gradient(circle at 8% 0%, #d9efeb 0, transparent 34%), var(--paper); }
    .shell { width: min(1120px, calc(100% - 32px)); margin: 0 auto; padding: 42px 0 64px; }
    header { display: flex; justify-content: space-between; align-items: end; gap: 24px; margin-bottom: 30px; }
    .eyebrow { color: var(--teal); font-weight: 700; letter-spacing: .12em; font-size: 12px; text-transform: uppercase; }
    h1, h2, p { margin-top: 0; } h1 { font-size: clamp(30px, 5vw, 54px); line-height: 1.1; letter-spacing: -.03em; margin-bottom: 10px; } h2 { font-size: 20px; margin-bottom: 4px; }
    .subtitle { color: var(--muted); max-width: 520px; margin: 0; }
    .layout { display: grid; grid-template-columns: 330px 1fr; gap: 22px; align-items: start; }
    .panel { background: rgba(255,255,255,.82); border: 1px solid rgba(220,230,226,.95); border-radius: 12px; box-shadow: 0 14px 36px rgba(23,50,77,.07); padding: 24px; }
    .form-panel { position: sticky; top: 20px; } label { display: block; font-weight: 700; margin: 17px 0 6px; } label:first-of-type { margin-top: 14px; }
    input, textarea, button { font: inherit; } input, textarea { width: 100%; border: 1px solid var(--line); border-radius: 7px; padding: 11px 12px; color: var(--ink); background: #fff; } textarea { min-height: 150px; resize: vertical; }
    button { border: 0; border-radius: 7px; padding: 10px 15px; cursor: pointer; font-weight: 700; } .primary { width: 100%; margin-top: 20px; color: #fff; background: var(--teal); } .primary:hover { background: #0b5e58; }
    .message { color: var(--coral); min-height: 24px; margin: 12px 0 0; font-size: 13px; }
    .summary { display: flex; justify-content: space-between; align-items: end; gap: 20px; border-bottom: 1px solid var(--line); padding-bottom: 22px; margin-bottom: 22px; } .summary h2 { font-size: 28px; }
    .goal { color: var(--muted); margin: 0; } .percent { color: var(--coral); font-size: 34px; font-weight: 800; line-height: 1; } .bar { height: 9px; overflow: hidden; background: #e8efec; border-radius: 20px; margin-top: 18px; } .bar > span { display: block; height: 100%; background: var(--coral); border-radius: inherit; transition: width .3s ease; }
    .stage { margin-top: 24px; } .stage-head { display: flex; justify-content: space-between; gap: 16px; align-items: baseline; } .stage-head h3 { margin: 0; font-size: 18px; } .stage-head span { color: var(--muted); font-size: 13px; } .objective { color: var(--muted); margin: 2px 0 12px; font-size: 13px; }
    .task { display: grid; grid-template-columns: 1fr auto; gap: 12px; align-items: center; border-top: 1px solid var(--line); padding: 14px 0; } .task-title { font-weight: 700; } .task-desc, .task-time { color: var(--muted); font-size: 13px; } .task-controls { display: flex; align-items: center; gap: 8px; } .task-controls input { width: 76px; padding: 7px 8px; } .task-controls button { color: #fff; background: var(--ink); padding: 7px 10px; } .task.done .task-title { color: var(--teal); text-decoration: line-through; }
    .empty { text-align: center; color: var(--muted); padding: 65px 20px; } .hidden { display: none; }
    @media (max-width: 760px) { .shell { padding-top: 25px; } header { display: block; } .layout { grid-template-columns: 1fr; } .form-panel { position: static; } .task { grid-template-columns: 1fr; } .task-controls { justify-content: flex-end; } }
  </style>
</head>
<body>
  <main class="shell">
    <header><div><div class="eyebrow">Learning Workspace</div><h1>把学习变成<br>看得见的进度。</h1><p class="subtitle">输入想学的内容，系统会自动拆成阶段和可执行任务。</p></div></header>
    <div class="layout">
      <section class="panel form-panel">
        <div class="eyebrow">Create plan</div><h2>新建学习计划</h2>
        <form id="plan-form"><label for="title">计划名称</label><input id="title" required placeholder="例如：Python 入门">
        <label for="goal">学习目标</label><input id="goal" required placeholder="例如：能独立完成小项目">
        <label for="content">学习内容</label><textarea id="content" required placeholder="每行一个知识点，也可以用分号分隔&#10;&#10;变量与类型&#10;条件与循环&#10;函数&#10;文件与异常"></textarea>
        <button class="primary" type="submit">生成学习计划</button><p id="message" class="message"></p></form>
      </section>
      <section id="workspace" class="panel hidden"><div id="plan-view"></div></section>
      <section id="empty" class="panel empty">还没有学习计划。<br>从左侧输入内容，开始拆解你的学习路径。</section>
    </div>
  </main>
  <script>
    const $ = (id) => document.getElementById(id);
    const message = (text = '') => $('message').textContent = text;
    async function request(url, options) { const response = await fetch(url, options); const data = await response.json(); if (!response.ok) throw new Error(data.error || '操作失败'); return data; }
    function render(plan) {
      $('empty').classList.add('hidden'); $('workspace').classList.remove('hidden');
      const stages = plan.stages.map(stage => `<div class="stage"><div class="stage-head"><h3>阶段 ${stage.id} · ${stage.title}</h3><span>${stage.tasks.filter(t => t.done).length}/${stage.tasks.length} 个任务完成</span></div><p class="objective">${stage.objective}</p>${stage.tasks.map(task => `<div class="task ${task.done ? 'done' : ''}"><div><div class="task-title">${task.id}. ${task.title}</div><div class="task-desc">${task.description}</div><div class="task-time">预计 ${task.estimated_minutes} 分钟</div></div><div class="task-controls"><input type="number" min="0" max="100" value="${task.progress}" aria-label="任务${task.id}进度"><button onclick="saveTask(${task.id}, this)">${task.done ? '已完成' : '更新'}</button></div></div>`).join('')}</div>`).join('');
      $('plan-view').innerHTML = `<div class="summary"><div><div class="eyebrow">Current plan</div><h2>${plan.title}</h2><p class="goal">目标：${plan.goal}</p></div><div class="percent">${plan.progress}%</div></div><div class="bar"><span style="width:${plan.progress}%"></span></div>${stages}`;
    }
    async function loadPlan() { try { render(await request('/api/plan')); } catch (_) {} }
    $('plan-form').addEventListener('submit', async (event) => { event.preventDefault(); message('正在生成...'); try { const plan = await request('/api/plan', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({title: $('title').value, goal: $('goal').value, content: $('content').value}) }); render(plan); message(''); } catch (error) { message(error.message); } });
    async function saveTask(id, button) { const input = button.parentElement.querySelector('input'); const progress = Math.max(0, Math.min(100, Number(input.value))); try { button.disabled = true; render(await request(`/api/tasks/${id}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({progress}) })); } catch (error) { message(error.message); } finally { button.disabled = false; } }
    loadPlan();
  </script>
</body></html>"""


class LearningHandler(BaseHTTPRequestHandler):
	def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
		body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
		self.send_response(status)
		self.send_header("Content-Type", "application/json; charset=utf-8")
		self.send_header("Content-Length", str(len(body)))
		self.end_headers()
		self.wfile.write(body)

	def read_json(self) -> dict[str, Any]:
		length = int(self.headers.get("Content-Length", "0"))
		return json.loads(self.rfile.read(length).decode("utf-8"))

	def do_GET(self) -> None:
		path = urlparse(self.path).path
		if path == "/":
			body = WEB_PAGE.encode("utf-8")
			self.send_response(200)
			self.send_header("Content-Type", "text/html; charset=utf-8")
			self.send_header("Content-Length", str(len(body)))
			self.end_headers()
			self.wfile.write(body)
		elif path == "/api/plan":
			try:
				self.send_json(plan_payload(load_plan()))
			except FileNotFoundError as error:
				self.send_json({"error": str(error)}, 404)
		else:
			self.send_json({"error": "页面不存在"}, 404)

	def do_POST(self) -> None:
		if urlparse(self.path).path != "/api/plan":
			self.send_json({"error": "接口不存在"}, 404)
			return
		try:
			data = self.read_json()
			plan = build_plan(data["title"].strip(), data["goal"].strip(), data["content"])
			save_plan(plan)
			self.send_json(plan_payload(plan))
		except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
			self.send_json({"error": str(error)}, 400)

	def do_PUT(self) -> None:
		match = re.fullmatch(r"/api/tasks/(\d+)", urlparse(self.path).path)
		if not match:
			self.send_json({"error": "接口不存在"}, 404)
			return
		try:
			data = self.read_json()
			update_task(int(match.group(1)), int(data["progress"]), int(data["progress"]) == 100)
			self.send_json(plan_payload(load_plan()))
		except (KeyError, TypeError, ValueError, json.JSONDecodeError, FileNotFoundError) as error:
			self.send_json({"error": str(error)}, 400)

	def log_message(self, format: str, *args: Any) -> None:
		return


def serve(port: int) -> None:
	server = HTTPServer(("127.0.0.1", port), LearningHandler)
	print(f"学习进度 UI 已启动：http://127.0.0.1:{port}")
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		print("\n服务器已停止。")
	finally:
		server.server_close()


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="根据学习内容自动分解学习进度")
	subparsers = parser.add_subparsers(dest="command", required=True)

	create = subparsers.add_parser("create", help="创建学习计划")
	create.add_argument("--title", required=True, help="计划名称")
	create.add_argument("--goal", required=True, help="学习目标")
	create.add_argument("--content", required=True, help="知识点，使用换行、分号或句号分隔")

	subparsers.add_parser("show", help="查看当前计划")
	serve_parser = subparsers.add_parser("serve", help="启动浏览器 UI")
	serve_parser.add_argument("--port", type=int, default=8000, help="服务端口，默认 8000")

	update = subparsers.add_parser("update", help="更新任务进度")
	update.add_argument("task_id", type=int, help="任务编号")
	update.add_argument("--progress", type=int, choices=range(0, 101), help="进度 0-100")
	update.add_argument("--done", action="store_true", help="标记为完成")
	return parser


def main() -> None:
	args = build_parser().parse_args()
	try:
		if args.command == "create":
			plan = build_plan(args.title, args.goal, args.content)
			save_plan(plan)
			print_plan(plan)
		elif args.command == "show":
			print_plan(load_plan())
		elif args.command == "update":
			if args.progress is None and not args.done:
				raise ValueError("请提供 --progress 或 --done。")
			update_task(args.task_id, args.progress, args.done)
			print_plan(load_plan())
		elif args.command == "serve":
			serve(args.port)
	except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
		print(f"错误：{error}")


if __name__ == "__main__":
	main()