#!/bin/sh

i=1

while [ $i -le `wc -l .env | awk '{print $1}'` ] ; do

    heroku config:add `head -$i .env | tail -1`

    i=`expr $i + 1`
    
done