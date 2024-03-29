package my_math

import (
	"errors"
	"fmt"
)

// func main() {
// 	DoMath(1, 2, "+")
// }

func DoMath(num1, num2 int, op string) (int, error) {
	switch op {
	case "+":
		return num1 + num2, nil
	case "-":
		return num1 - num2, nil
	case "*":
		return num1 * num2, nil
	case "/":
		if num2 == 0 {
			return 0, errors.New("0による徐算")
		}
		return num1 / num2, nil
	default:
		return 0, fmt.Errorf("未知の演算子 %s", op)
	}
}
