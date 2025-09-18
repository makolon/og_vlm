from typing import List, Optional

import omnigibson as og
from omnigibson.macros import gm
gm.ENABLE_OBJECT_STATES = True

def make_env(activity: str, robot: str = "r1pro", headless: bool = True):
    """
    Create an OmniGibson environment and load a BEHAVIOR activity (defined by BDDL).
    """
    # Utility for creation (Evaluator also used internally)
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
        # Minimal fallback (example for future API changes)
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
    (Optional) Get an RGB image from the environment and return as a base64 string.
    Returns None if not available.
    """
    try:
        robot = env.robots[0]
        if hasattr(robot, "get_camera_images"):
            rgb = robot.get_camera_images()["rgb"]
        else:
            return None
        import cv2
        import base64
        _, buf = cv2.imencode(".png", rgb[..., ::-1])
        return base64.b64encode(buf.tobytes()).decode("utf-8")
    except Exception:
        return None


def bddl_success_fraction(env) -> float:
    """
    Returns the fraction of satisfied BDDL predicates (partial score).
    Depends on OmniGibson's Metric / TerminationCondition; if not available, returns 0/1 approximation.
    """
    # 1) Use TaskMetric if available
    try:
        from omnigibson.learning.metrics.task_metric import TaskMetric
        metric = TaskMetric(env=env)
        frac = metric.compute()["predicate_success_fraction"]
        return float(frac)
    except Exception:
        pass

    # 2) If TerminationCondition (predicate_goal) is exposed, get from there
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
