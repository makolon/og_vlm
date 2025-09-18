from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import os

import omnigibson as og
from omnigibson.macros import gm
gm.ENABLE_OBJECT_STATES = True

def make_env(activity: str, robot: str = "r1pro", headless: bool = True):
    """
    OmniGibson 環境を生成し，BEHAVIOR の活動（BDDL定義）をロードする．
    """
    # 生成ユーティリティ（Evaluator も内部で使用）
    try:
        from omnigibson.learning.utils.config_utils import generate_basic_environment_config
        cfg = generate_basic_environment_config(
            task="behavior",
            scene="behavior",
            activity=activity,
            robots=[robot],
            use_task_defaults=True,
        )
    except Exception:
        # 最小フォールバック（将来の API 変更に備えた例）
        cfg = {
            "task": {"type": "BehaviorTask", "activity_name": activity},
            "scene": {"type": "InteractiveTraversableScene"},
            "robots": [{"type": robot}],
        }

    env = og.Environment(configs=cfg, headless=headless)
    env.reset()
    return env


def list_scene_names(env, max_items: int = 64) -> List[str]:
    names = []
    try:
        for obj in env.scene.objects:
            if hasattr(obj, "name"):
                names.append(obj.name)
    except Exception:
        pass
    names = list(dict.fromkeys(names))
    return names[:max_items]


def try_rgb_image_b64(env) -> Optional[str]:
    """
    （任意）環境から RGB 画像を取得し，base64 文字列を返す．
    取得できない場合は None を返す．
    """
    try:
        robot = env.robots[0]
        if hasattr(robot, "get_camera_images"):
            rgb = robot.get_camera_images()["rgb"]
        else:
            return None

        import cv2, base64
        _, buf = cv2.imencode(".png", rgb[..., ::-1])
        return base64.b64encode(buf.tobytes()).decode("utf-8")
    except Exception:
        return None


def bddl_success_fraction(env) -> float:
    """
    BDDL の充足割合（部分点）を返す．
    OmniGibson の Metric / TerminationCondition に依存し，取得できない場合は 0/1 近似．
    """
    # 1) TaskMetric があれば利用
    try:
        from omnigibson.learning.metrics.task_metric import TaskMetric
        metric = TaskMetric(env=env)
        frac = metric.compute()["predicate_success_fraction"]
        return float(frac)
    except Exception:
        pass

    # 2) TerminationCondition（predicate_goal）が expose していればそこから取得
    try:
        terminations = getattr(env.task, "termination_conditions", [])
        for tc in terminations:
            if tc.__class__.__name__.lower().startswith("predicate"):
                info = tc.get_termination(env.task, env)
                done, extra = info if isinstance(info, tuple) else (False, {})
                frac = extra.get("predicate_success_fraction", None)
                if frac is not None:
                    return float(frac)
    except Exception:
        pass

    return 0.0
