for num in 0 10 20 30 40 50 60 70 80 90 100; do
  for state in charging discharging; do
    src="../icons/svg/idle/$num.svg"
    dest="../icons/svg/$state/$num.svg"
    sym="${state}_symbol.svg"
    perl svg_merge.pl $dest $sym $src
  done
done
