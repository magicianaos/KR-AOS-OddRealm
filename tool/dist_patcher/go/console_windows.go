//go:build windows

package main

import "syscall"

// Windows 콘솔을 UTF-8(65001)로 전환해 한글이 깨지지 않게 한다.
func enableUTF8Console() {
	k := syscall.NewLazyDLL("kernel32.dll")
	for _, n := range []string{"SetConsoleOutputCP", "SetConsoleCP"} {
		_, _, _ = k.NewProc(n).Call(uintptr(65001))
	}
}
