a=11
# -lt is less than operator
  
#Iterate the loop until a less than 10
while [ $a -lt 21 ]
do 
    # Print the values
    python pacman.py -p ApproximateQAgent -g DirectionalGhost -a extractor=SimpleExtractor --localizedShield 1 --lookAhead $a -x 0 -y 300 -n 320 -l scosGridTraps.lay
      
    # increment the value
    a=`expr $a + 1`
done
