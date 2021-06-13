#!/bin/bash  

cd main
git add --all  .
#read -p "bash shell script " desc
git commit -m "desc" nse_intraday.ipynb
git push
