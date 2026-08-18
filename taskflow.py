import streamlit as st
from datetime import date

# ==================================================
# PAGE SETTINGS
# ==================================================
st.set_page_config(page_title="TaskFlow Scheduler", page_icon="✅", layout="wide")

st.title("✅ TaskFlow Scheduler")
st.subheader("Priority Task Manager — Heap + Stack + Queue")
st.write(
    "This project manages tasks using a **Min-Heap** (priority queue by deadline), "
    "a **Stack** (undo last action), and a **Queue** (completed-task history), "
    "all implemented from scratch."
)

# ==================================================
# 1. MIN-HEAP CLASS (array-based, built from scratch)
#    Priority = earlier deadline first, then higher urgency
# ==================================================
class MinHeap:
    def __init__(self):
        self.heap = []  # list of task dicts

    def _priority_key(self, task):
        # Smaller date = higher priority; urgency 3 (High) sorts before 1 (Low)
        urgency_rank = {"High": 0, "Medium": 1, "Low": 2}
        return (task["deadline"], urgency_rank[task["urgency"]])

    def _swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

    def push(self, task):
        self.heap.append(task)
        self._sift_up(len(self.heap) - 1)

    def _sift_up(self, i):
        while i > 0:
            parent = (i - 1) // 2
            if self._priority_key(self.heap[i]) < self._priority_key(self.heap[parent]):
                self._swap(i, parent)
                i = parent
            else:
                break

    def pop_min(self):
        """Remove and return the highest-priority task (root of heap)."""
        if not self.heap:
            return None
        min_task = self.heap[0]
        last = self.heap.pop()
        if self.heap:
            self.heap[0] = last
            self._sift_down(0)
        return min_task

    def _sift_down(self, i):
        n = len(self.heap)
        while True:
            left, right = 2 * i + 1, 2 * i + 2
            smallest = i
            if left < n and self._priority_key(self.heap[left]) < self._priority_key(self.heap[smallest]):
                smallest = left
            if right < n and self._priority_key(self.heap[right]) < self._priority_key(self.heap[smallest]):
                smallest = right
            if smallest == i:
                break
            self._swap(i, smallest)
            i = smallest

    def remove_by_name(self, name):
        """Remove a specific task by name (rebuilds heap)."""
        remaining = [t for t in self.heap if t["name"] != name]
        removed = len(remaining) != len(self.heap)
        self.heap = []
        for t in remaining:
            self.push(t)
        return removed

    def sorted_view(self):
        """Non-destructive: returns tasks sorted by priority without popping."""
        return sorted(self.heap, key=self._priority_key)

    def is_empty(self):
        return len(self.heap) == 0


# ==================================================
# 2. STACK CLASS (undo last action)
# ==================================================
class Stack:
    def __init__(self):
        self.items = []

    def push(self, action):
        self.items.append(action)

    def pop(self):
        if not self.items:
            return None
        return self.items.pop()

    def is_empty(self):
        return len(self.items) == 0

    def peek(self):
        return self.items[-1] if self.items else None


# ==================================================
# 3. QUEUE CLASS (FIFO — completed task history)
# ==================================================
class Queue:
    def __init__(self):
        self.items = []

    def enqueue(self, item):
        self.items.append(item)

    def dequeue(self):
        if not self.items:
            return None
        return self.items.pop(0)

    def is_empty(self):
        return len(self.items) == 0

    def as_list(self):
        return list(self.items)


# ==================================================
# 4. SESSION STATE INITIALIZATION
# ==================================================
if "heap" not in st.session_state:
    st.session_state.heap = MinHeap()
if "undo_stack" not in st.session_state:
    st.session_state.undo_stack = Stack()
if "completed_queue" not in st.session_state:
    st.session_state.completed_queue = Queue()

heap = st.session_state.heap
undo_stack = st.session_state.undo_stack
completed_queue = st.session_state.completed_queue

# ==================================================
# 5. ADD TASK FORM
# ==================================================
st.header("1️⃣ Add a Task")

col1, col2, col3 = st.columns(3)
with col1:
    task_name = st.text_input("Task name", placeholder="e.g. Submit assignment")
with col2:
    deadline = st.date_input("Deadline", min_value=date.today())
with col3:
    urgency = st.selectbox("Urgency", ["High", "Medium", "Low"])

if st.button("➕ Add Task"):
    if not task_name.strip():
        st.warning("⚠️ Please enter a task name.")
    else:
        task = {"name": task_name.strip(), "deadline": deadline, "urgency": urgency}
        heap.push(task)
        undo_stack.push(("add", task))
        st.success(f"Added: {task_name} (Deadline: {deadline}, Urgency: {urgency})")

# ==================================================
# 6. UNDO LAST ACTION (STACK)
# ==================================================
st.header("2️⃣ Undo Last Action")
if st.button("↩️ Undo"):
    last_action = undo_stack.pop()
    if last_action is None:
        st.info("Nothing to undo.")
    else:
        action_type, task = last_action
        if action_type == "add":
            heap.remove_by_name(task["name"])
            st.success(f"Undid: removed '{task['name']}' from the task list.")
        elif action_type == "complete":
            heap.push(task)
            # remove it from completed history (it was the most recent one added)
            if completed_queue.items and completed_queue.items[-1]["name"] == task["name"]:
                completed_queue.items.pop()
            st.success(f"Undid: '{task['name']}' moved back to pending tasks.")

# ==================================================
# 7. PENDING TASKS — HEAP VIEW (highest priority first)
# ==================================================
st.header("3️⃣ Pending Tasks (Priority Order — Min-Heap)")

if heap.is_empty():
    st.info("No pending tasks. Add one above.")
else:
    ordered_tasks = heap.sorted_view()
    for i, t in enumerate(ordered_tasks, 1):
        urgency_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[t["urgency"]]
        cols = st.columns([5, 2, 2, 2])
        cols[0].write(f"**{i}. {t['name']}**")
        cols[1].write(f"📅 {t['deadline']}")
        cols[2].write(f"{urgency_icon} {t['urgency']}")
        if cols[3].button("✅ Complete", key=f"complete_{t['name']}_{i}"):
            heap.remove_by_name(t["name"])
            completed_queue.enqueue(t)
            undo_stack.push(("complete", t))
            st.rerun()

    top_task = heap.sorted_view()[0]
    st.success(f"🎯 Next task to do (heap root): **{top_task['name']}**")

# ==================================================
# 8. COMPLETED TASKS — QUEUE VIEW (FIFO history)
# ==================================================
st.header("4️⃣ Completed Task History (FIFO Queue)")

if completed_queue.is_empty():
    st.info("No tasks completed yet.")
else:
    for i, t in enumerate(completed_queue.as_list(), 1):
        st.write(f"{i}. ✔️ {t['name']} — completed (was due {t['deadline']}, {t['urgency']} urgency)")

# ==================================================
# 9. STRUCTURE INSPECTOR (for demo/learning purposes)
# ==================================================
with st.expander("🔍 Internal Data Structure State (for demo)"):
    st.write("**Heap array (internal order, not sorted view):**")
    st.json([{"name": t["name"], "deadline": str(t["deadline"]), "urgency": t["urgency"]} for t in heap.heap])
    st.write("**Undo stack (top = last item):**")
    st.json([{"action": a[0], "task": a[1]["name"]} for a in undo_stack.items])
    st.write("**Completed queue (front = first completed):**")