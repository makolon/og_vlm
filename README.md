# OmniGibson × VLM (GPT‑5 / Gemini 2.5 Pro) Task Planning + BDDL Evaluation

This minimal implementation loads BEHAVIOR activities (defined by BDDL) on **OmniGibson**, generates high-level **Task Plans** using VLM (`GPT-5` or `gemini-2.5-pro`), executes them with a simple Executor (Semantic Action Primitives or teleport fallback), and aggregates success rates (ratio of satisfied predicates) using **BDDL** for research purposes.

> Note: This code is a **research prototype**. API names may change due to version differences in OmniGibson / BEHAVIOR.
> If Semantic Action Primitives (SAP) are available, they are used; otherwise, the system automatically falls back to "teleport execution".
> Precise robot-level control and strict motion planning can be replaced as needed.

---

## 1. Setup

### 1.1 Dependencies

- OmniGibson (including BEHAVIOR assets)  
  Official instructions: https://behavior.stanford.edu/getting_started/installation.html
- Python libs (minimum required)

```bash
pip install -r requirements.txt
```

> Installing OmniGibson and downloading assets may take time. Please pay attention to GPU / VRAM requirements.

### 1.2 API Keys

Set the environment variables:

```bash
export OPENAI_API_KEY="..."       # GPT-5 (OpenAI Responses API)
export GEMINI_API_KEY="..."       # Gemini 2.5 Pro (google-genai)
```

> Gemini uses the `google-genai` SDK (both Developer API and Vertex are supported).

---

## 2. Usage (Evaluation Execution)

### Evaluation with a Single Activity (5 Episodes)

```bash
python run_eval.py   --provider openai --model gpt-5   --activity "pick_up_trash"   --episodes 5   --robot r1pro   --exec primitives
```

Or with Gemini:

```bash
python run_eval.py   --provider gemini --model gemini-2.5-pro   --activity "pick_up_trash"   --episodes 5   --robot r1pro   --exec primitives
```

**Main argument descriptions**

- `--provider`: `openai` or `gemini`
- `--model`: `gpt-5` (OpenAI Responses API), `gemini-2.5-pro` (Gemini)
- `--activity`: BEHAVIOR activity name (e.g., `pick_up_trash`, `store_food`, `prepare_lunch_box`)
- `--episodes`: Number of trials
- `--robot`: `r1pro` or `tiago` recommended (SAP supported)
- `--exec`: `primitives` (recommended) / `teleport` (fallback)

> **primitives** execution requires an environment where Starter Semantic Action Primitives work (R1/Tiago & compatible controllers).
> If not available, specify `--exec teleport` (minimal prototype that directly manipulates state to satisfy goals).

---

## 3. Overview of Mechanism

1. **Environment Generation**: Load `BehaviorTask` in OmniGibson (initial/goal conditions based on BDDL)
2. **Observation → Prompt**: List candidate objects and receptacles in the scene, input them to VLM along with the activity name
  - (Optional) Attach camera images if available
3. **VLM Planning**: Generate a high-level plan in strict JSON format (e.g., `GRASP`, `PLACE_INSIDE`, `OPEN`)
4. **Execution**: Sequentially execute the plan with SAP (if available); otherwise, approximate execution with teleport
5. **Evaluation**: Obtain the **ratio of satisfied predicates** from the environment using BDDL and calculate the success rate for each episode

---

## 4. Known Limitations and Extension Points

- **Camera Observation**: The API for obtaining images varies by environment and robot. This implementation works mainly with text; images are optional.
- **Object Naming**: Fuzzy matching is used to resolve target names from VLM output to scene IDs.
- **Executor**: Use `primitives` whenever possible; `teleport` is a simple fallback for research purposes.
- **Strict Success Evaluation**: Prefer OmniGibson's task metrics (`TaskMetric`) if available; otherwise, obtain/approximate the ratio of satisfied predicates via internal API.

---

## 5. References (Implementation Basis)

- **BDDL and BEHAVIOR Definition**: BEHAVIOR tasks are defined by BDDL (predicate logic) and include initial and goal conditions.
  Success is partially scored by the **ratio of satisfied BDDL predicates**. (Official documentation / challenge guidelines)
- **Evaluator / Metrics**: OmniGibson's Evaluator / TaskMetric enables policy evaluation and video export.
- **Semantic Action Primitives**: High-level operations (e.g., `GRASP`, `PLACE_INSIDE`) are available for R1 / Tiago, etc.

---

## 6. Example Commands

```bash
# 10 trials with teleport execution fallback
python run_eval.py --provider openai --model gpt-5   --activity "store_food" --episodes 10 --exec teleport

# Try Tiago + primitives execution
python run_eval.py --provider gemini --model gemini-2.5-pro   --activity "prepare_lunch_box" --robot tiago --exec primitives
```

---

## 7. Disclaimer

- Model names and SDK API specifications may be updated. Please adjust `vlm_clients.py` as needed.
- This implementation is for research purposes and may include physically unnatural operations (teleport).
- Additional configuration may be required depending on GPU / OmniGibson version differences.
