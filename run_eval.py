import argparse
import json
from typing import Dict, Any

from tqdm import trange

from og_vlm_planning.vlm_clients import get_planner
from og_vlm_planning.og_env import make_env, list_scene_names, try_rgb_image_b64, bddl_success_fraction
from og_vlm_planning.executors import TeleportExecutor, PrimitiveExecutor


def exec_step(executor, step: Dict[str, Any]):
    op = step.get("op", "").upper()
    if op == "NAVIGATE_TO":
        return executor.navigate_to(step["target"])
    if op == "GRASP":
        return executor.grasp(step["target"])
    if op == "PLACE_ON_TOP":
        return executor.place_on_top(step["object"], step["receptacle"])
    if op == "PLACE_INSIDE":
        return executor.place_inside(step["object"], step["receptacle"])
    if op == "OPEN":
        return executor.open(step["target"])
    if op == "CLOSE":
        return executor.close(step["target"])
    if op == "RELEASE":
        return executor.release()
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", type=str, default="openai", choices=["openai", "gemini"])
    ap.add_argument("--model", type=str, default="gpt-5")
    ap.add_argument("--activity", type=str, default="putting_food_in_fridge")
    ap.add_argument("--episodes", type=int, default=5)
    ap.add_argument("--robot", type=str, default="R1Pro")
    ap.add_argument("--exec", dest="executor", type=str, default="primitives", choices=["primitives", "teleport"])
    ap.add_argument("--temperature", type=float, default=0.1)
    args = ap.parse_args()

    # env
    print("[info] Environment setup...")
    env = make_env(activity=args.activity, robot=args.robot)

    # planner
    print("[info] Initializing planner...")
    planner = get_planner(provider=args.provider, model=args.model, temperature=args.temperature)

    # executor
    if args.executor == "primitives":
        try:
            executor = PrimitiveExecutor(env)
        except Exception as e:
            print(f"[warn] PrimitiveExecutor unavailable ({e}); falling back to TeleportExecutor")
            executor = TeleportExecutor(env)
    else:
        executor = TeleportExecutor(env)

    success = 0
    frac_sum = 0.0

    for _ in trange(args.episodes, desc="episodes"):
        env.reset()

        # context
        catalog = list_scene_names(env)
        image_b64 = try_rgb_image_b64(env)

        # plan
        print("[info] Planning with context:", {
            "activity": args.activity,
            "robot": args.robot,
            "scene": env.scene.name if hasattr(env.scene, "name") else "unknown",
            "objects": catalog,
            "image_b64": image_b64 is not None,
        })
        plan = planner.plan(activity=args.activity, catalog=catalog, notes="", image_b64=image_b64)
        print("[info] Plan:", plan)

        # execute
        for step in plan.plan:
            res = exec_step(executor, step.dict())
            print(f"[step] {step.op} {step} => {res}")
            if res is None:
                print(f"[skip] unknown op: {step.op}")
                continue

        # evaluate by BDDL fraction
        frac = bddl_success_fraction(env)
        frac_sum += frac
        if frac >= 0.999:
            success += 1

    print(json.dumps({
        "activity": args.activity,
        "episodes": args.episodes,
        "success_rate": success / args.episodes,
        "avg_bddl_fraction": frac_sum / args.episodes,
        "provider": args.provider,
        "model": args.model,
        "executor": args.executor,
        "robot": args.robot,
    }, indent=2))


if __name__ == "__main__":
    main()
