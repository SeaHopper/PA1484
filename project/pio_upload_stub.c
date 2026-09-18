/*
 * PlatformIO's Upload target requires a linkable program even though this
 * project deploys Python files. This inert program is never flashed;
 * platformio/deploy.py replaces the uploader with flash_app().
 */

unsigned uxTopUsedPriority = 0;

void call_user_start_cpu0(void)
{
    for (;;) {
    }
}
