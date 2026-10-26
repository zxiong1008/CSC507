Here is the code extracted and formatted as code blocks, corresponding to the commands and programs shown in your terminal images:

### 1. Bash Script (`numbers.sh`)

```bash
cat << 'EOF' > numbers.sh
#!/bin/bash
for ((i=1; i<=1000; i++))
do
    echo $RANDOM >> file1.txt
done
EOF

```

### 2. Execution & Verification Commands

```bash
chmod +x numbers.sh
./numbers.sh
cat file1.txt | head -n 10

```

### 3. Python Program to Generate `file2.txt`

```python
import random

def main():
    with open("file2.txt", "w") as f:
        for _ in range(1000):
            f.write(f"{random.randint(0, 32767)}\n")

if __name__ == "__main__":
    main()

```

### 4. Word and Line Count

```bash
wc *

```