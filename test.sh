data=$(ps aux | grep "python tehnoskarb.py" | wc -l);
echo $data;
if [ $data == "2" ]; then
  echo "Process is running. ok.."
else
  echo "Process is not running.";
  echo "starting process ...";
  ./start.sh;
	
fi
