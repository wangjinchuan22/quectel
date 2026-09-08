"""学习进度分解系统。

用法示例：
	python t1.py create --title "Python 入门" --goal "能写出小项目" \
		--content "变量与类型\n条件与循环\n函数\n文件与异常"
	python t1.py show
	python t1.py update 1 --done
	python t1.py update 2 --progress 60
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


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


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="根据学习内容自动分解学习进度")
	subparsers = parser.add_subparsers(dest="command", required=True)

	create = subparsers.add_parser("create", help="创建学习计划")
	create.add_argument("--title", required=True, help="计划名称")
	create.add_argument("--goal", required=True, help="学习目标")
	create.add_argument("--content", required=True, help="知识点，使用换行、分号或句号分隔")

	subparsers.add_parser("show", help="查看当前计划")

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
	except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
		print(f"错误：{error}")


if __name__ == "__main__":
	main()