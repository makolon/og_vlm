from typing import Dict, Any, List, Optional, Tuple
import numpy as np

class ExecutionResult:
    def __init__(self, success: bool, info: Dict[str, Any]):
        self.success = success
        self.info = info


class TeleportExecutor:
    """
    最小フォールバック：対象オブジェクトを receptacle の AABB 上にテレポート配置するなど，
    物理挙動を省略して目標を満たしにいく簡易実行器（研究用）．
    """
    def __init__(self, env):
        self.env = env

    def _obj_by_name(self, name: str):
        # 名寄せ（部分一致）
        candidates = [o for o in self.env.scene.objects if hasattr(o, "name") and name.lower() in o.name.lower()]
        return candidates[0] if candidates else None

    def _aabb_center_top(self, obj):
        # AABB -> 中心上面座標（簡易）
        try:
            aabb = obj.aabb
            center = ( (aabb[0][0] + aabb[1][0]) / 2.0,
                       (aabb[0][1] + aabb[1][1]) / 2.0,
                        aabb[1][2] )
            return np.array(center) + np.array([0.0, 0.0, 0.05])
        except Exception:
            # フォールバック
            return np.array([0.0, 0.0, 1.0])

    def _set_pose(self, obj, pos, orn=None):
        try:
            obj.set_position(pos)  # EntityPrim API
        except Exception:
            # 代替 API 名の可能性
            if hasattr(obj, "set_world_position"):
                obj.set_world_position(pos)
        # 回転は省略（必要に応じて set_orientation を追加）

    def grasp(self, name: str):
        # テレポート実行では grasp は no-op とし，次の place で位置決めする
        return ExecutionResult(True, {"op": "GRASP", "target": name})

    def place_on_top(self, obj_name: str, receptacle_name: str):
        o = self._obj_by_name(obj_name)
        r = self._obj_by_name(receptacle_name)
        if o is None or r is None:
            return ExecutionResult(False, {"reason": "object or receptacle not found"})
        pos = self._aabb_center_top(r)
        self._set_pose(o, pos)
        return ExecutionResult(True, {"op": "PLACE_ON_TOP", "object": obj_name, "receptacle": receptacle_name})

    def place_inside(self, obj_name: str, receptacle_name: str):
        # 近似：同様に receptacle 上方へ移動（厳密な「内側」充足は receptacle 形状に依存）
        return self.place_on_top(obj_name, receptacle_name)

    def open(self, name: str):
        # 近似：開閉はスキップ（必要ならジョイントを操作）
        return ExecutionResult(True, {"op": "OPEN", "target": name})

    def close(self, name: str):
        return ExecutionResult(True, {"op": "CLOSE", "target": name})

    def navigate_to(self, target: str):
        return ExecutionResult(True, {"op": "NAVIGATE_TO", "target": target})

    def release(self):
        return ExecutionResult(True, {"op": "RELEASE"})


class PrimitiveExecutor:
    """
    Starter Semantic Action Primitives を利用してプランを実行．
    未導入環境では ImportError になり得るため，利用側で try/except して Teleport にフォールバックしてください．
    """
    def __init__(self, env, robot=None):
        from omnigibson.action_primitives.starter_semantic_action_primitives import StarterSemanticActionPrimitives
        self.env = env
        self.robot = robot or env.robots[0]
        self.sap = StarterSemanticActionPrimitives(scene=env.scene, robot=self.robot)

    def _nearest_by_name(self, name: str):
        # SAP はオブジェクト参照を受け取ることが多いので，名寄せして最も近いものを返す例
        objs = [o for o in self.env.scene.objects if hasattr(o, "name") and name.lower() in o.name.lower()]
        if not objs:
            return None
        # 距離順
        base_pos = self.robot.get_position()
        objs.sort(key=lambda o: np.linalg.norm(o.get_position() - base_pos))
        return objs[0]

    def navigate_to(self, target: str):
        tgt = self._nearest_by_name(target)
        if tgt is None:
            return ExecutionResult(False, {"reason": "target not found"})
        for action in self.sap.NAVIGATE_TO(tgt):
            self.env.step(action)
        return ExecutionResult(True, {"op": "NAVIGATE_TO", "target": target})

    def grasp(self, target: str):
        obj = self._nearest_by_name(target)
        if obj is None:
            return ExecutionResult(False, {"reason": "object not found"})
        for action in self.sap.GRASP(obj):
            self.env.step(action)
        return ExecutionResult(True, {"op": "GRASP", "target": target})

    def place_on_top(self, obj_name: str, receptacle_name: str):
        obj = self._nearest_by_name(obj_name)
        rec = self._nearest_by_name(receptacle_name)
        if obj is None or rec is None:
            return ExecutionResult(False, {"reason": "object or receptacle not found"})
        for action in self.sap.PLACE_ON_TOP(obj, rec):
            self.env.step(action)
        return ExecutionResult(True, {"op": "PLACE_ON_TOP", "object": obj_name, "receptacle": receptacle_name})

    def place_inside(self, obj_name: str, receptacle_name: str):
        obj = self._nearest_by_name(obj_name)
        rec = self._nearest_by_name(receptacle_name)
        if obj is None or rec is None:
            return ExecutionResult(False, {"reason": "object or receptacle not found"})
        for action in self.sap.PLACE_INSIDE(obj, rec):
            self.env.step(action)
        return ExecutionResult(True, {"op": "PLACE_INSIDE", "object": obj_name, "receptacle": receptacle_name})

    def open(self, name: str):
        tgt = self._nearest_by_name(name)
        if tgt is None:
            return ExecutionResult(False, {"reason": "target not found"})
        for action in self.sap.OPEN(tgt):
            self.env.step(action)
        return ExecutionResult(True, {"op": "OPEN", "target": name})

    def close(self, name: str):
        tgt = self._nearest_by_name(name)
        if tgt is None:
            return ExecutionResult(False, {"reason": "target not found"})
        for action in self.sap.CLOSE(tgt):
            self.env.step(action)
        return ExecutionResult(True, {"op": "CLOSE", "target": name})

    def release(self):
        for action in self.sap.RELEASE():
            self.env.step(action)
        return ExecutionResult(True, {"op": "RELEASE"})
