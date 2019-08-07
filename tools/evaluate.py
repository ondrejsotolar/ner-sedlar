#! /usr/bin/env python
# vim: set encoding=utf-8

import sys


def load_entities(filename):
    entities = {}
    with open(filename, 'r') as f:
        for line in f:
            start, length, cat, text = line.rstrip('\n').split('\t')
            start = int(start)
            length = int(length)
            entities[(start, start + length)] = (text, cat)
    return entities


def intersects(gold, start, end):
    for (s1, e1) in gold:
        if (start > s1 and start < e1) or (end > s1 and end < e1):
            del gold[(s1, e1)]
            return True
    return False


def print_result_line(title, tp, fp, total, old):
    precision = float(tp) / (tp + fp) * 100
    recall = float(tp) / total * 100
    f_measure = 2 * (precision * recall) / (precision + recall)
    impr = ''
    if old > 0:
        impr = '      %+.2f' % (f_measure - old)
    print('%-20s     %.2f /  %.2f / %.2f%s' % (title + ':',
                                               precision,
                                               recall,
                                               f_measure,
                                               impr))
    return f_measure


def write_file(filename, data):
    with open(filename, 'w') as f:
        for (start, text) in data:
            f.write('%d\t%s\n' % (start, text))


def read_prev(prev_file, n):
    try:
        with open(prev_file, 'r') as f:
            return tuple([float(f.readline()) for _ in range(n)])
    except IOError:
        return tuple([0 for _ in range(n)])
    except ValueError:
        return tuple([0 for _ in range(n)])


def mk_prev_fname(output):
    return '.%s.prev_result' % output


def filter_whole(lst):
    """Filter out partial entities."""
    return dict((k, v) for k, v in lst.items() if v[1] != 'P')


def run_eval(title, gold, real, old_f, save=False):
    tp_texts = []
    fp_texts = []
    fn_texts = dict([(k, t) for (k, (t, c)) in gold.iteritems()])

    total_count = len(gold)
    found_count = len(real)
    tp = 0
    fp = 0
    almost_tp = 0
    almost_fp = 0

    for ((start, end), (text, _)) in sorted(real.iteritems()):
        if (start, end) in gold:
            del fn_texts[(start, end)]
            tp += 1
            almost_tp += 1
            tp_texts.append((start, text))
        elif intersects(gold, start, end):
            almost_tp += 1
            fp += 1
            fp_texts.append((start, text))
        else:
            almost_fp += 1
            fp += 1
            fp_texts.append((start, text))

    print '\n## %s' % title
    print 'Found %d entities in gold, %d in real data' % (total_count, found_count)
    print '                     Precision / Recall / F-measure   Diff'
    f1 = print_result_line('Exact bounds', tp, fp, total_count, old_f[0])
    f2 = print_result_line('Intersection', almost_tp, almost_fp, total_count, old_f[1])
    print ""

    if save:
        write_file('true_positives.txt', tp_texts)
        write_file('false_positives.txt', fp_texts)
        write_file('false_negatives.txt',
                   [(s, e) for ((s, e), t)
                                in sorted(fn_texts.iteritems())])

    return f1, f2


def main(gold_file, real_file):
    all_gold = load_entities(gold_file)
    gold = filter_whole(all_gold)
    all_real = load_entities(real_file)
    real = filter_whole(all_real)
    prev_file_name = mk_prev_fname(real_file)

    old_f1, old_f2, old_f3, old_f4 = read_prev(prev_file_name, 4)
    f1, f2 = run_eval('Whole entities', gold, real, (old_f1, old_f2), True)
    f3, f4 = run_eval('Subentities', all_gold, all_real, (old_f3, old_f4), True)

    with open(prev_file_name, 'w') as f:
        f.write('%f\n%f\n%f\n%f\n' % (f1, f2, f3, f4))


if __name__ == '__main__':
    gold_file = '../data/cnec2.0/dtest.txt'
    real_file = 'cnec_output.txt'
    if len(sys.argv) != 3 and len(sys.argv) != 1:
        print("Usage: %s GOLD_FILE RESULT_FILE" % sys.argv[0])
        sys.exit(1)
    if len(sys.argv) == 3:
        gold_file, real_file = sys.argv[1:]
    main(gold_file, real_file)
