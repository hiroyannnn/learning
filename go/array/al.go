package array

import "fmt"

func main() {
	x := make([]int, 10)
	preCap := cap(x)
	for i := 1; i < 10000; i++ {
		x = append(x, i)
		if preCap != cap(x) {
			fmt.Printf("[Size = %d] Capacity = %d \n", i, cap(x))
			preCap = cap(x)
		}
	}
}
