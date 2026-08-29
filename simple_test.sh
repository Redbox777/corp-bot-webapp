#!/bin/bash
echo "🚀 Starting simple load test..."
start=$(date +%s)

for i in {1..50}; do
    curl -s http://localhost:5000/api/player/test_$i > /dev/null &
    curl -s -X POST http://localhost:5000/api/click/test_$i > /dev/null &
done

wait
end=$(date +%s)
duration=$((end - start))

echo "✅ Test completed in ${duration} seconds"
echo "   Made 100 requests"
echo "   Average: $((100 / duration)) requests/second"
