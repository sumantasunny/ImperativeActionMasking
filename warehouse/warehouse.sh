a=11
# -lt is less than operator
  
#Iterate the loop until a less than 10
while [ $a -lt 21 ]
do 
    # Print the values
    python warehouse.py -p ApproximateQAgent -g ForkTruckPath -a extractor=SimpleExtractor --localizedShield 1 --lookAhead $a -x 0 -y 300 -n 320 -l warehouse.lay
      
    # increment the value
    a=`expr $a + 1`
done
