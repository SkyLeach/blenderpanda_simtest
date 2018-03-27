import sys
import os
import logging
import textwrap
import inspect
from code import InteractiveConsole
import re
import string
import pprint
import traceback
# venv/requires imports
import pyperclip
# panda imports (dylib/venv)
from panda3d.core import TextNode
from panda3d.core import Vec3
from direct.showbase import DirectObject
from direct.gui.DirectGui import DirectFrame
from direct.gui.DirectGui import DirectEntry
from direct.gui.DirectGui import DGG  # DirectGuiGlobals
from direct.gui.DirectGui import DirectScrolledList
from direct.gui.OnscreenText import OnscreenText
from completer import completePython

# module-level logger
logger = logging.getLogger(__name__)

# --- define your settings here ---
# output debug informations
DEBUG = True
# command which causes the help to be shown
HELP_COMMAND       = 'help'
# all of the following must be eighter a single character or None
# None means its allways (except on exclude) active
# call the python interpreter in this character
PYTHON_PRE         = None
# dont call the python interpreter on this character
PYTHON_PRE_EXCLUDE = '!'
# after what time should keys be read from the command line
# if set to None, taskMgr.add will be used instead of taskMgr.doMethodLater
TERMINAL_TASK_TIME = None
AUTOCOMPLETER = True
AUTOCOMPLETER_INFOTEXT_COLOR = (0.8, 0.8, 0.8, 1.0)
HELP_INFOTEXT_COLOR = (0.8, 1.0, 0.8, 1.0)
# --- variables for the panda3d console ----
# default color of the panda3d font
CONSOLE_DEFAULT_COLOR = (1, 1, 1, 1)
# toggle key to show/hide the panda3d console
PANDA3D_CONSOLE_TOGGLE_KEY       = "`"
PANDA3D_CONSOLE_AUTOCOMPLETE_KEY = "tab"
PANDA3D_CONSOLE_AUTOHELP_KEY    = "f1"
# font to be used
PANDA3D_CONSOLE_FONT            = '/Library/Fonts/Verdana.ttf'
# PANDA3D_CONSOLE_FONT = 'data/interactiveConsole/vera.ttf'
# this value has to be determined manually,
# it is used to calculate number of characters on a line
PANDA3D_CONSOLE_FONT_WIDTH       = 0.5
# the size & position of the console window
PANDA3D_CONSOLE_SCALE            = 0.04
PANDA3D_CONSOLE_HORIZONTAL_POS   = 0.15
PANDA3D_CONSOLE_HORIZONTAL_SIZE  = 1.9
PANDA3D_CONSOLE_VERTICAL_POS     = 0.05
PANDA3D_CONSOLE_VERTICAL_SIZE    = 1.9
# to change the alignment of the console
# look into the panda3d.py def windowEvent


# --- things after this line should not be changed ---

# some constants
INPUT_GUI = 1
INPUT_CONSOLE = 2
OUTPUT_PYTHON = 3

CONSOLE_MESSAGE = ''' --- Game Debug Interface ---
root game object: gameroot
--------------------------'''

class ConsoleOutput(DirectScrolledList):
    # list of dslitems that are also commands
    _command_history = []

    @property
    def history(self):
        return self._history

    def __init__(self, *args, **kwargs):
        if 'testme' in kwargs and kwargs['testme']:
            if 'items' not in kwargs:
                kwargs['items'] = []
#             for testitm in [ 'This is', 'a test', 'of DSL' ]:
#                 kwargs['items'].append(testitm)
        super().__init__(**kwargs)

class ConsoleWindow(DirectObject.DirectObject):
    console_output = None
    gui_key = PANDA3D_CONSOLE_TOGGLE_KEY
    autocomplete_key = PANDA3D_CONSOLE_AUTOCOMPLETE_KEY
    autohelp_key = PANDA3D_CONSOLE_AUTOHELP_KEY
    # change size of text and number of characters on one line
    # scale of frame (must be small (0.0x)
    scale = PANDA3D_CONSOLE_SCALE
    # to define a special font, if loading fails the default font is used
    # (without warning)
    font = PANDA3D_CONSOLE_FONT
    fontWidth = PANDA3D_CONSOLE_FONT_WIDTH
    # frame position and size (vertical & horizontal)
    h_pos   = PANDA3D_CONSOLE_HORIZONTAL_POS
    h_size  = PANDA3D_CONSOLE_HORIZONTAL_SIZE
    # v_size + v_pos should not exceed 2.0, else parts of the interface
    # will not be visible
    # space above the frame (must be below 2.0, best between 0.0 and 1.0)
    v_pos   = PANDA3D_CONSOLE_VERTICAL_POS
    # vertical size of the frame (must be at max 2.0, best between 0.5 and 2.0)
    v_size           = PANDA3D_CONSOLE_VERTICAL_SIZE
    linelength       = int((h_size/scale - 5) / fontWidth)
    textBuffer       = list()
    MAX_BUFFER_LINES = 5000
    commandPos       = 0
    _iconsole        = None
    _commandBuffer   = ''
    logger.debug("max number of characters on a length:", linelength)
    numlines          = int(v_size/scale - 5)
    defaultTextColor  = (0.0, 0.0, 0.0, 1.0)
    autoCompleteColor = (0.9, 0.9, 0.9, 1.0)
    consoleFrame      = None
    commandList       = []
    maxCommandHistory = 10000
    textBufferPos     = -1
    clipboardTextLines = None
    clipboardTextRaw = None

    def __init__(self, parent):
        global base
        if not logger.isEnabledFor(logging.DEBUG):
            global CONSOLE_MESSAGE
            CONSOLE_MESSAGE = '''
----------------- Ship's Interface version 3.0.9_749 -------------------
Direct Ship Interface Enabled.
Please use caution.  Irresponsible use of this console may result in the ship's AI refusing access to this interface.

type 'help' for basic commands.
-------------------------------------------------------------------------'''

        # change up from parent/IC
        self.parent = parent
        localenv = globals()
        localenv['gameroot'] = self.parent
        self._iconsole = customConsoleClass(localsEnv=localenv)

        # line wrapper
        self.linewrap = textwrap.TextWrapper()
        self.linewrap.width = self.linelength

        # calculate window size
        # left   = (self.h_pos) / self.scale
        # right  = (self.h_pos + self.h_size) / self.scale
        # bottom = (self.v_pos) / self.scale
        # top    = (self.v_pos + self.v_size) /self.scale

        # panda3d interface
        self.consoleFrame = DirectFrame(
            relief     = DGG.GROOVE,
            frameColor = (200, 200, 200, 0.5),
            scale      = self.scale,
            frameSize  = (
                0,
                self.h_size / self.scale,
                0,
                self.v_size / self.scale))

        self.windowEvent(base.win)
        fixedWidthFont = None
        try:
            # try to load the defined font
            fixedWidthFont = parent.loader.loadFont(self.font)
        except Exception:
            traceback.print_exc()
            # if font is not valid use default font
            logger.warn('could not load the defined font %s" % str(self.font')
            fixedWidthFont = DGG.getDefaultFont()

        # text lines
        self._visibleLines = list(
            OnscreenText(
                parent    = self.consoleFrame,
                text      = "",
                pos       = (1, -i+3+self.numlines),
                align     = TextNode.ALeft,
                mayChange = 1,
                scale     = 1.0,
                fg        = self.defaultTextColor)
            for i in range(self.numlines))
        map(lambda x: x.setFont(fixedWidthFont), self._visibleLines)

        # text entry line
        self.consoleEntry = DirectEntry(
            self.consoleFrame,
            text        = "",
            command     = self.submitTrigger,
            width       = self.h_size/self.scale - 2,
            pos         = (1, 0, 1.5),
            initialText = "",
            numLines    = 1,
            focus       = 1,
            entryFont   = fixedWidthFont)

        # self.console_output = ConsoleOutput(testme=True)
        self.echo(CONSOLE_MESSAGE)
        self.clipboard = pyperclip

    def windowEvent(self, window):
        """
        This is a special callback.
        It is called when the panda window is modified.
        """
        wp = window.getProperties()
        width = wp.getXSize() / float(wp.getYSize())
        height = wp.getYSize() / float(wp.getXSize())
        if width > height:
            height = 1.0
        else:
            width = 1.0
        # aligned to center
        consolePos = Vec3(-self.h_size/2, 0, -self.v_size/2)
        # aligned to left bottom
        # consolePos = Vec3(-width+self.h_pos, 0, -height+self.v_pos)
        # aligned to right top
        # consolePos = Vec3(width-self.h_size, 0, height-self.v_size)
        # set position
        self.consoleFrame.setPos(consolePos)

    def submitTrigger(self, cmdtext):
        # set to last message
        # clear line
        self.consoleEntry.enterText('')
        self.focus()
        # add text entered to user command list & remove oldest entry
        self.commandList.append(cmdtext)
        self.commandPos += 1
        self._commandBuffer = ''
        logger.debug('CP {}'.format(self.commandPos))
        # push to interp
        for text, pre, color in self._iconsole.push(cmdtext):
            self.echo(text, pre, color)

    # set up console controls
    def mapControls(self):
        hidden = self.consoleFrame.isHidden()
        self.consoleEntry['focus'] != hidden
        if hidden:
            self.ignoreAll()
        else:
            self.accept('page_up', self.scroll, [-5])
            self.accept('page_up-repeat', self.scroll, [-5])
            self.accept('page_down', self.scroll, [5])
            self.accept('page_down-repeat', self.scroll, [5])
            self.accept('window-event', self.windowEvent)
            self.accept('arrow_up', self.scrollCmd, [-1])
            self.accept('arrow_down', self.scrollCmd, [1])
            self.accept(self.gui_key, self.toggleConsole)
            self.accept('escape', self.toggleConsole)
            self.accept(self.autocomplete_key , self.autocomplete)
            self.accept(self.autohelp_key , self.autohelp)

            # accept v, c and x, where c & x copy's the whole console text
            # messenger.toggleVerbose()
            # for osx use ('meta')
            if sys.platform == 'darwin':
                self.accept('meta', self.unfocus)
                self.accept('meta-up', self.focus)
                self.accept('meta-c', self.copy)
                self.accept('meta-x', self.cut)
                self.accept('meta-v', self.paste)
            # for windows use ('control')
            if sys.platform == 'win32' or sys.platform == 'linux2':
                self.accept('control', self.unfocus)
                self.accept('control-up', self.focus)
                self.accept('control-c', self.copy)
                self.accept('control-x', self.cut)
                self.accept('control-v', self.paste)

    # toggle the gui console
    def toggleConsole(self, hide=False):
        if hide:
            self.consoleFrame.hide()
            self.ignoreAll()
            # express hide, don't call setControls()
            return

        if self.consoleFrame.is_hidden():
            self.consoleFrame.show()
            self.parent.setControls(self)
        else:
            self.consoleFrame.hide()
            self.ignoreAll()
            self.parent.setControls()

    def scroll(self, step):
        newpos = self.textBufferPos + step
        if newpos < 0 or newpos >= len(self.textBuffer):
            # no... no... I no think so
            return
        self.textBufferPos = newpos
        self.redrawConsole()

    def redrawConsole(self):
        windowstart = max(self.textBufferPos-len(self._visibleLines)+1, 0)
        windowend = min(
            len(self._visibleLines)+windowstart,
            len(self.textBuffer)
        )
        logger.debug('windowS: {} WindowE: {}'.format(windowstart, windowend))
        for lineNumber, (lineText, color) in \
                enumerate(self.textBuffer[
                    windowstart:
                    windowend]):
            logger.debug(
                "LN {}, LEN {}".format(
                    lineNumber,
                    len(self.textBuffer)
                )
            )
            self._visibleLines[lineNumber].setText(lineText)
            self._visibleLines[lineNumber]['fg'] = color

    def scrollCmd(self, step):
        if not self.commandList:  # 0 or null - nothing to scroll
            return
        # should we update a temp buffer?
        if self.commandPos == len(self.commandList):
            if step > 0:
                self.consoleEntry.set(self._commandBuffer)
                return
            else:
                tmp = self.consoleEntry.get()
                if self.commandList[-1] != tmp:
                    self._commandBuffer = tmp
        self.commandPos += step
        if self.commandPos >= len(self.commandList):
            self.commandPos = len(self.commandList)-1
            self.consoleEntry.set(self._commandBuffer)
            self.consoleEntry.setCursorPosition(
                len(self.commandList[self.commandPos]))
        elif self.commandPos < 0:
            self.commandPos = -1
            # No need to change anything, can't go past the beginning
            return
        # finally, just set it
        self.consoleEntry.set(self.commandList[self.commandPos])
        self.consoleEntry.setCursorPosition(
            len(self.commandList[self.commandPos]))

    def autocomplete(self):
        currentText = self.consoleEntry.get()
        currentPos = self.consoleEntry.guiItem.getCursorPosition()
        newText = self._iconsole.autocomplete(currentText, currentPos)
        if newText[-1] and newText[-1] != currentText:
            self.consoleEntry.set(newText[-1])
            self.consoleEntry.setCursorPosition(len(newText))

    def autohelp(self):
        currentText = self.consoleEntry.get()
        currentPos = self.consoleEntry.guiItem.getCursorPosition()
        self.parent.autohelp(currentText, currentPos)

    def unfocus(self):
        self.consoleEntry['focus'] = 0

    def focus(self):
        self.consoleEntry['focus'] = 1

    def copy(self):
        copy = self.consoleEntry.get()
        pyperclip.copy(copy)

    def paste(self):
        oldCursorPos = self.consoleEntry.guiItem.getCursorPosition()
        self.clipboardTextRaw = pyperclip.paste()

        # compose new text line
        oldText = self.consoleEntry.get()
        newText = oldText[0:oldCursorPos] + self.clipboardTextRaw + oldText[oldCursorPos:]

        self.clipboardTextLines = newText.split(os.linesep)

        for i in range(len(self.clipboardTextLines)-1):
            currentLine = self.clipboardTextLines[i]
            # we only want printable characters
            currentLine = re.sub(r'[^' + re.escape(string.printable[:95]) + ']', "", currentLine)

            # set new text and position
            self.consoleEntry.set(currentLine)
            self.submitTrigger(currentLine)
        currentLine = self.clipboardTextLines[-1]
        currentLine = re.sub(r'[^' + re.escape(string.printable[:95]) + ']', "", currentLine)
        self.consoleEntry.set(currentLine)
        self.consoleEntry.setCursorPosition(len(self.consoleEntry.get()))
        self.focus()

    def cut(self):
        pyperclip.copy(self.consoleEntry.get())
        self.consoleEntry.enterText('')
        self.focus()

    def echo(self, output, pre='*', color=defaultTextColor):
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('output: {}'.format(pprint.pformat(output)))
        for line in output.split('\n'):
            fmtline = "{}{}".format(pre,line)
            logger.debug(fmtline)
            if len(line) > 0:
                self.write_to_panel(fmtline, color)

    def write_to_panel(self, output, color=defaultTextColor):
    # remove not printable characters (which can be input by console input)
        output = re.sub(r'[^%s]' % re.escape(string.printable[:95]),
                "", output)
        logger.debug('write_to_panel: output="{}"'.format(output))
        splitLines = self.linewrap.wrap(output)
        logger.debug('write_to_panel: splitLines="{}"'.format(splitLines))
        for line in splitLines:
            self.textBuffer.append([line, color])
            if len(self.textBuffer) > self.MAX_BUFFER_LINES:
                self.textBuffer.pop(0)
            else:
                self.textBufferPos+=1

        self.redrawConsole()


class OutputFilter:
    "Cache the stdout text so we can analyze it before returning it"
    def __init__(self):
        self.reset()
    def reset(self):
        self.out = []
    def write(self,line):
        self.out.append(line)
    def flush(self):
        output = '\n'.join(self.out).rstrip()
        self.reset()
        return output

class customConsoleClass(InteractiveConsole):
    inputColor    = (1.0,0.8,1.0,1.0)
    outputColor = (0.8,1.0,1.0,1.0)
    def __init__(self, localsEnv=globals()):
        InteractiveConsole.__init__(self, localsEnv)
        errcount=1
        while errcount:
            try:
                logger.debug("customConsoleClass", localsEnv)
                break
            except BlockingIOError as be:
                if errcount > 5:
                    raise
                else:
                    errcount+=1
        self.consoleLocals = localsEnv

        # catch the output of the interactive interpreter
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.cache = OutputFilter()

        self.help()

    def help(self):
        text = " ------ InteractiveConsole ------ \n"
        if PYTHON_PRE is None:
            text += """- direct entry enabled"""
        else:
            text += """- use '%s' in front of a line to send it to the interactiveConsole component
- example: %sfor i in xrange(10):    # no spaces between the ! and the 'for'
- example: %s        print i
- example: %s <enter>\n"""    % (PYTHON_PRE,PYTHON_PRE,PYTHON_PRE,PYTHON_PRE)
        text += """- BUGS     : do not try to call something like 'while True:'
        you will not be able to break it, you must at least include 'Task.step()'
%s            : autocomplete commands
%s             : help"""%(
            PANDA3D_CONSOLE_AUTOCOMPLETE_KEY, PANDA3D_CONSOLE_AUTOHELP_KEY
       )
        return text

    def get_output(self):
        sys.stdout = self.cache
        sys.stderr = self.cache

    def return_output(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def push(self, input):
        output = list()
        output.append(["%s" % input, '>>> ', self.inputColor])

        # execute on interactiveConsole console
        self.get_output()
        InteractiveConsole.push(self, input)
        self.return_output()

        resultText = self.cache.flush()

        if len(resultText) > 0:
            output.append(["%s" % resultText, '> ', self.outputColor])

        return output

    def autocomplete(self, pythonText, currentCursorPos):
        newText = pythonText
        printText = None

        pythonTestSplit = pythonText.split(' ')
        env = self.consoleLocals
        term = completePython(env, pythonText)

        # if the entered name is uniq, use autocomplete
        if len(term) == 1:
            newTextList = pythonTestSplit[0:-1]
            newTextList.append(term[0])
            newText = ' '.join(newTextList)
        # output the list of available names
        elif len(term) > 1:
            printText = str(term)

        return newText, printText

    def autohelp(self, pythonText, currentCursorPos):
        # read the docstring
        docString = self.push("%s.__doc__" % pythonText)
        if len(docString) == 1 or \
             'Traceback' in docString[1][0] or \
             'SyntaxError' in docString[-1][0]:
            logger.debug("discarding __doc__ of %s l(%i): %s " % (pythonText, len(docString), docString))
            docString = None
        else:
            logger.debug("accepting doc string %s" % docString)
            docString = docString[1][0]

        # read the first five lines of the sourcecode
        self.push("import inspect")
        inspectString = self.push(
            "inspect.getsourcelines({})[0][0:6]".format(pythonText))
        if 'SyntaxError' in inspectString[1][0] or \
                'Traceback' in inspectString[1][0] or \
                len(inspectString) > 6:
            logger.debug("discarding inspect of %s l(%i): %s" % (
                pythonText,
                len(inspectString),
                inspectString)
            )
            inspectString = None
        else:
            logger.debug("accepting inspect string %s" % inspectString)
            inspectString = inspectString[1][0]

        # if no docstring found
        if docString is not None:
            lines = docString
        else:
            if inspectString is not None:
                lines = inspectString
            else:
                lines = 'no sourcecode & docstring found', ''
        logger.debug("test", lines)
        # return the help text
        helpText = ''.join(list(str(line) for line in lines))
        # exec("helpText = ''.join(%s)" % str(lines))
        # helpText = ''.join(lines)
        helpText = "--- help for %s ---\n" % (pythonText) + helpText
        return helpText
