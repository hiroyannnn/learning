package my_math

import (
	"testing"

	"lerning/my_math"
)

func TestMath_DoMath(t *testing.T) {
	my_math.DoMath()
	data := []struct {
		name     string
		num1     int
		num2     int
		op       string
		expected int
		errMsg   string
	}{
		{"add", 1, 2, "+", 3, ""},
		{"sub", 1, 2, "-", -1, ""},
		{"mul", 1, 2, "*", 2, ""},
		{"div", 1, 2, "/", 0, ""},
		{"div", 1, 0, "/", 0, "divide by zero"},
	}

	for _, d := range data {
		t.Run(d.name, func(t *testing.T) {
			actual, err := my_math.DoMath(d.num1, d.num2, d.op)
			if err != nil && err.Error() != d.errMsg {
				t.Errorf("expected error %s, got %s", d.errMsg, err.Error())
			}
			if actual != d.expected {
				t.Errorf("expected %d, got %d", d.expected, actual)
			}
		})
	}
}
