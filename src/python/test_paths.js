// test_paths.js - створіть окремий файл
const { spawn } = require('child_process');
const path = require('path');

const pythonPath = path.join(__dirname, 'src/python/api_bridge_fixed.py');
console.log(`Python path: ${pythonPath}`);
console.log(`CWD: ${path.dirname(pythonPath)}`);

const proc = spawn('python', ['-c', `
import sys
import os
print("Python:", sys.executable)
print("CWD:", os.getcwd())
print("Path:", sys.path)
`], {
  cwd: path.dirname(pythonPath)
});

proc.stdout.on('data', (d) => console.log(d.toString()));
proc.stderr.on('data', (d) => console.error(d.toString()));