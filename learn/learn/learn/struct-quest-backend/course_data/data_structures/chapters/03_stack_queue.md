# 栈和队列

## 学习目标

理解受限线性表的思想；掌握栈的 LIFO 特性和队列的 FIFO 特性；能够实现顺序栈、链栈、循环队列和链队列，并说明典型应用。

## 栈

栈只允许在表尾进行插入和删除。允许操作的一端称为栈顶，另一端称为栈底。入栈和出栈遵循后进先出。

栈常用于函数调用、括号匹配、表达式求值、递归转非递归和深度优先搜索。顺序栈需要判断栈满和栈空；链栈通常不需要预设容量。

## 队列

队列允许在队尾插入，在队头删除，遵循先进先出。队列常用于广度优先搜索、任务调度、缓冲区和消息队列。

顺序队列会出现“假溢出”：数组前部已有空位，但队尾指针到达数组末端。循环队列通过取模运算复用空间，常用 `(rear + 1) % maxsize == front` 表示队满，此时会牺牲一个存储单元。

## 代码示例

```python
class CircularQueue:
    def __init__(self, size):
        self.data = [None] * size
        self.front = 0
        self.rear = 0

    def is_empty(self):
        return self.front == self.rear

    def is_full(self):
        return (self.rear + 1) % len(self.data) == self.front
```

## 易错点

循环队列的队满条件、队空条件和有效长度计算经常混淆。递归问题可以用栈解释，但不是所有栈应用都必须写递归。
